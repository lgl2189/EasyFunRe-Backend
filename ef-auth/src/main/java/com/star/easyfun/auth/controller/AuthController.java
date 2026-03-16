package com.star.easyfun.auth.controller;

import com.star.easyfun.auth.pojo.dbo.UserBasicDBO;
import com.star.easyfun.auth.pojo.dto.UserLoginDTO;
import com.star.easyfun.auth.pojo.dto.UserLoginResultDTO;
import com.star.easyfun.auth.service.DeviceService;
import com.star.easyfun.auth.service.JWTCoreService;
import com.star.easyfun.auth.service.UserBasicService;
import com.star.easyfun.auth.service.impl.SmsServiceImpl;
import com.star.easyfun.auth.util.RequestUtil;
import com.star.easyfun.common.constant.CommonRequestHeader;
import com.star.easyfun.common.pojo.dto.JWTPairDTO;
import com.star.easyfun.common.pojo.dto.Result;
import com.star.easyfun.common.util.ResultUtil;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.mapstruct.ap.internal.util.Strings;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.time.LocalTime;
import java.util.HashMap;
import java.util.Map;

/**
 * @author ：Star
 * @description ：与验证身份有关的请求，本Controller的前缀为微服务前缀"/auth"
 * @date ：2026 3月 03 19:57
 */
@Validated
@RestController
@RequiredArgsConstructor
public class AuthController {
    private final UserBasicService userBasicService;
    private final SmsServiceImpl smsServiceImpl;
    private final JWTCoreService jWTCoreService;
    private final DeviceService deviceService;
    private static final Logger logger = LogManager.getLogger(AuthController.class);

    @GetMapping("/login/sms")
    public Result getLoginSms(@Validated(UserLoginDTO.SmsGetCode.class) UserLoginDTO userLoginDTO, HttpServletRequest request) {
        String ip = RequestUtil.getIpAddr(request);
        String fingerprint = RequestUtil.getFingerprint(request);
        if (!smsServiceImpl.postSmsCode(userLoginDTO.getPhone(), ip, fingerprint)) {
            return ResultUtil.fail_20004("24小时内获取验证码次数过多，请之后再试");
        }
        return ResultUtil.success_10000("获取短信验证码成功");
    }

    @PostMapping("/login/sms")
    public Result loginBySms(@Validated(UserLoginDTO.PhoneLogin.class) @RequestBody UserLoginDTO loginDTO,
                             @RequestHeader(value = CommonRequestHeader.HEADER_FINGERPRINT) String fingerprint,
                             @RequestHeader(value = CommonRequestHeader.HEADER_DEVICE_ID, required = false) String deviceId,
                             HttpServletRequest request) {
        // 如果手机号未已注册，自动注册
        if (!userBasicService.checkPhoneExist(loginDTO.getPhone())) {
            boolean registSuccess = userBasicService.register(loginDTO.getPhone());
            if (!registSuccess) {
                return ResultUtil.fail_50000("注册失败，出现系统内部错误");
            }
        }
        String ip = RequestUtil.getIpAddr(request);
        if (!smsServiceImpl.verifySmsCode(loginDTO.getPhone(), ip, fingerprint, loginDTO.getSmsCode())) {
            return ResultUtil.fail_20005("验证码错误");
        }
        // Sms验证成功，开始登陆
        // 获取用户信息
        UserBasicDBO userBasicDBO = userBasicService.login(loginDTO);
        if (userBasicDBO == null) {
            return ResultUtil.fail_50000("系统内部错误，未找到您的帐户，请尝试重新登陆或联系客服");
        }

        String userId = userBasicDBO.getUserId().toString();
        boolean isNewDeviceId = false;
        if (Strings.isNotEmpty(deviceId) && deviceService.isDeviceIdExist(userId, deviceId)) {
            deviceService.cacheDeviceId(userId, deviceId);
        }
        else {
            deviceId = deviceService.generateDeviceId(userId);
            isNewDeviceId = true;
        }
        JWTPairDTO jwtPairDTO;
        try {
            jwtPairDTO = jWTCoreService.generateJWTPair(userBasicDBO, deviceId);
        }
        catch (Exception e) {
            logger.error("ef-auth中，产生jwt时出现错误，错误由generateJWT方法抛出", e);
            return ResultUtil.fail_50000("系统内部错误，请稍后重试或联系客服");
        }
        UserLoginResultDTO userLoginResultDTO = new UserLoginResultDTO(jwtPairDTO, deviceId, isNewDeviceId)
                .setUserId(userId);
        return ResultUtil.success_10000(userLoginResultDTO, "登录成功");
    }

    @PostMapping("/login/password")
    public Result loginByPassword(@Validated(UserLoginDTO.PassLogin.class) @RequestBody UserLoginDTO loginDTO) {
        // TODO: 密码登录功能未完成
        return ResultUtil.success_10000(LocalTime.now(), "密码登录功能未完成");
    }

    @PostMapping("/login/token")
    public Result loginByToken(@RequestHeader(CommonRequestHeader.HEADER_USER_ID) String userId) {
        // 如果请求能到达这里，而不是被网关拦截，说明AccessToken是有效的
        Map<String, Object> result = new HashMap<>();
        result.put("userId", userId);
        return ResultUtil.success_10000(result, "通过AccessToken登录成功");
    }

    @PostMapping("/refresh/token")
    public Result refreshToken(@RequestHeader(CommonRequestHeader.HEADER_REFRESH_TOKEN) String refreshToken,
                               @RequestHeader(CommonRequestHeader.HEADER_DEVICE_ID) String deviceId,
                               @RequestHeader(CommonRequestHeader.HEADER_USER_ID) String userId) throws Exception {
        JWTPairDTO jwtPairDTO = jWTCoreService.refreshToken(refreshToken, deviceId);
        if (jwtPairDTO == null) {
            return ResultUtil.fail_30001("RefreshToken无效");
        }
        // 刷新DeviceId的过期时间
        deviceService.cacheDeviceId(userId, deviceId);
        return ResultUtil.success_10000(jwtPairDTO, "刷新AccessToken成功");
    }

    @PostMapping("/logout")
    public Result deactivateToken(@RequestHeader(CommonRequestHeader.HEADER_AUTHORIZATION) String accessToken,
                                  @RequestHeader(CommonRequestHeader.HEADER_REFRESH_TOKEN) String refreshToken,
                                  @RequestHeader(CommonRequestHeader.HEADER_DEVICE_ID) String deviceId,
                                  @RequestHeader(CommonRequestHeader.HEADER_USER_ID) String userId) {
        if (Strings.isEmpty(accessToken)) {
            return ResultUtil.fail_30001("AccessToken为空");
        }
        if (Strings.isEmpty(refreshToken)) {
            return ResultUtil.fail_30001("RefreshToken为空");
        }
        String rawAccessToken = accessToken.substring(7);
        boolean isSuccess = jWTCoreService.deactivateToken(rawAccessToken, refreshToken, deviceId);
        deviceService.removeDeviceId(userId, deviceId);
        if (!isSuccess) {
            return ResultUtil.fail_30002("Token 格式错误或解析失败");
        }
        return ResultUtil.success_10000(null, "无效化Token成功");
    }
}