package com.star.easyfun.gateway.filter;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.star.easyfun.common.constant.CommonRedisKey;
import com.star.easyfun.common.constant.CommonRequestHeader;
import com.star.easyfun.common.pojo.dto.Result;
import com.star.easyfun.common.pojo.dto.TokenPayLoad;
import com.star.easyfun.common.service.JWTCommonService;
import com.star.easyfun.common.util.JWTHelper;
import com.star.easyfun.common.util.ResultUtil;
import com.star.easyfun.gateway.constant.RequestUrlConstant;
import lombok.RequiredArgsConstructor;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.cloud.gateway.support.ServerWebExchangeUtils;
import org.springframework.core.io.buffer.DataBufferUtils;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.ReactiveSecurityContextHolder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;

/**
 * @author ：Star
 * @description ：    用于拦截所有请求并进行鉴权
 * @date ：2026 3月 03 20:03
 */
// 选择手动创建对象，是因为如果将Filter作为SpringBean，Spring会自动将其加入Spring的过滤器链
// 会导致过滤器同时存在于Spring的过滤器链和SpringSecurity的过滤器链，最终导致每个请求被处理两次
// 目前没有找到方式在WebFlux中手动关闭一个过滤器的自动注册
@RequiredArgsConstructor
public class AuthFilter implements WebFilter {

    private final ObjectMapper objectMapper;
    private final JWTCommonService jwtCommonService;
    private final JWTHelper jwtHelper;
    private final RedisTemplate<String, Object> redisTemplate;

    private final AntPathMatcher antPathMatcher = new AntPathMatcher();
    private static final Logger logger = LogManager.getLogger(AuthFilter.class);

    @Override
    public Mono<Void> filter(@NonNull ServerWebExchange exchange, @NonNull WebFilterChain chain) {
        String currentPath = exchange.getRequest().getPath().value();
        for (String path : RequestUrlConstant.gatewaySecurityIgnoreUrlList) {
            if (antPathMatcher.match(path, currentPath)) {
                return chain.filter(exchange);
            }
        }
        HttpHeaders headers = exchange.getRequest().getHeaders();
        String authHeader = headers.getFirst(CommonRequestHeader.HEADER_AUTHORIZATION);
        if (authHeader == null) {
            return buildResponse(exchange, ResultUtil.fail_30001("未提供Token"));
        }
        // 统一转小写，兼容前端传bearer（小写）的情况
        String lowerAuthHeader = authHeader.toLowerCase();
        if (!lowerAuthHeader.startsWith(CommonRequestHeader.HEADER_AUTHORIZATION_PREFIX)) {
            return buildResponse(exchange, ResultUtil.fail_30002("Token 无效，格式错误，Bearer前缀缺失"));
        }
        // 先截取，再trim，兼容多空格的情况
        String accessToken = authHeader.substring(7).trim();
        // 校验AccessToken是否为空
        if (accessToken.isEmpty()) {
            return buildResponse(exchange, ResultUtil.fail_30002("未提供Token，为空字符串"));
        }
        // 处理Token验证逻辑
        Jwt jwt = jwtCommonService.validateToken(accessToken);
        if (jwt == null) {
            return buildResponse(exchange, ResultUtil.fail_30003("Token验证失败，Token已失效"));
        }
        TokenPayLoad tokenPayLoad;
        try {
            tokenPayLoad = jwtHelper.getPayloadFromJWT(jwt);
        }
        catch (JsonProcessingException e) {
            logger.error("ef-gateway中，jwt解析时出现JsonProcessingException错误，导致jwt解析失败", e);
            return buildResponse(exchange, ResultUtil.fail_30003("Token验证失败，Token已失效"));
        }
        // 检查该Token是否被黑名单记录
        String deviceId = headers.getFirst(CommonRequestHeader.HEADER_DEVICE_ID);
        String userId = tokenPayLoad.getUserId();
        if(redisTemplate.hasKey(CommonRedisKey.getJwtBlackAccessTokenKey(userId,deviceId))){
            return buildResponse(exchange, ResultUtil.fail_30003("该Token已登出或被封禁"));
        }
        Authentication authentication = new UsernamePasswordAuthenticationToken(
                tokenPayLoad.getUserId(),
                null,
                tokenPayLoad.getAuthorities()
        );
        return ServerWebExchangeUtils.cacheRequestBody(exchange, (serverHttpRequest) -> {
            // 构建新请求，仅添加userId请求头
            ServerHttpRequest mutatedRequest = serverHttpRequest.mutate()
                    .header(CommonRequestHeader.HEADER_USER_ID, tokenPayLoad.getUserId())
                    .build();
            ServerWebExchange mutatedExchange = exchange.mutate().request(mutatedRequest).build();

            // 传递认证信息并继续过滤器链
            return chain.filter(mutatedExchange)
                    .contextWrite(ReactiveSecurityContextHolder.withAuthentication(authentication))
                    .onErrorResume(e -> {
                        logger.error("ef-gateway中，认证过程中发生异常", e);
                        return buildResponse(exchange, ResultUtil.fail_50000("出现内部错误，认证失败"));
                    });
        });
        // 暂时不实现内部签名
//        return ServerWebExchangeUtils.cacheRequestBody(exchange, (serverHttpRequest) -> {
//            // 从缓存的请求中提取载荷
//            return getPayloadFromRequest(serverHttpRequest)
//                    .flatMap(payloadStr -> {
//                        try {
//                            ServerHttpRequest mutatedRequest;
//                            if (!Strings.isNullOrEmpty(payloadStr)) {
//                                String hmacSHA256 = jwtCommonService.generateHmacSHA256(
//                                        objectMapper.writeValueAsString(payloadStr)
//                                );
//                                // 构建新的 exchange，传递缓存的请求体
//                                mutatedRequest = serverHttpRequest.mutate()
//                                        .header(CommonRequestHeader.HEADER_USER_ID, tokenPayLoad.getUserId()) // 根据userId类型调整
//                                        .header(CommonRequestHeader.HEADER_INTERNAL_SIGN, hmacSHA256) // 放入内部签名头
//                                        .build();
//
//                            }
//                            else {
//                                // 没有请求体不进行内部签名
//                                mutatedRequest = serverHttpRequest.mutate()
//                                        .header(CommonRequestHeader.HEADER_USER_ID, tokenPayLoad.getUserId()) // 根据userId类型调整
//                                        .build();
//                            }
//
//                            ServerWebExchange mutatedExchange = exchange.mutate().request(mutatedRequest).build();
//                            return chain.filter(mutatedExchange)
//                                    .contextWrite(ReactiveSecurityContextHolder.withAuthentication(authentication));
//                        }
//                        catch (JsonProcessingException e) {
//                            logger.error("ef-gateway中，生成HMAC SHA256签名时出现JsonProcessingException错误", e);
//                            return buildResponse(exchange, ResultUtil.fail_50000("出现内部错误，签名失败"));
//                        }
//                    })
//                    .onErrorResume(e -> {
//                        logger.error("ef-gateway中，认证或签名过程中发生异常", e);
//                        return buildResponse(exchange, ResultUtil.fail_50000("出现内部错误，认证或签名失败"));
//                    });
//        });
    }

    /**
     * 构建响应（通用方法）
     *
     * @param exchange 请求响应交换对象
     * @param result   响应体
     * @return Mono<Void> 响应结果
     */
    private Mono<Void> buildResponse(ServerWebExchange exchange, Result result) {
        ServerHttpResponse response = exchange.getResponse();
        // 1. 设置状态码
        response.setStatusCode(HttpStatus.OK);
        // 2. 设置响应体格式（JSON）
        response.getHeaders().setContentType(MediaType.APPLICATION_JSON);
        try {
            byte[] jsonBytes = objectMapper.writeValueAsBytes(result);
            return response.writeWith(Mono.just(response.bufferFactory().wrap(jsonBytes)));
        }
        catch (JsonProcessingException e) {
            // 兜底：JSON序列化失败时返回简单文本响应
            response.getHeaders().setContentType(MediaType.TEXT_PLAIN);
            byte[] errorBytes = ("系统异常：" + e.getMessage()).getBytes();
            return response.writeWith(Mono.just(response.bufferFactory().wrap(errorBytes)));
        }
    }

    /**
     * 从请求中提取载荷，与OpenFeign过滤器中的逻辑一致
     *
     * @param request 请求对象
     * @return Mono<String> 载荷
     */
    private Mono<String> getPayloadFromRequest(ServerHttpRequest request) {
        return DataBufferUtils.join(request.getBody())
                .map(dataBuffer -> {
                    byte[] bytes = new byte[dataBuffer.readableByteCount()];
                    dataBuffer.read(bytes);
                    DataBufferUtils.release(dataBuffer);
                    return new String(bytes, StandardCharsets.UTF_8);
                })
                .defaultIfEmpty("");
    }
}