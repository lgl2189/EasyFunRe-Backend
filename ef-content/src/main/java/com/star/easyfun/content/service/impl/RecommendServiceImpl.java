package com.star.easyfun.content.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.star.easyfun.content.client.RecommendClient;
import com.star.easyfun.content.constant.RedisKeyConstant;
import com.star.easyfun.content.mapper.ContentInteractionRecordMapper;
import com.star.easyfun.content.mapper.ContentPostMapper;
import com.star.easyfun.content.mapper.RecommendParamMapper;
import com.star.easyfun.content.pojo.dbo.ContentInteractionRecordDBO;
import com.star.easyfun.content.pojo.dbo.ContentPostDBO;
import com.star.easyfun.content.pojo.dbo.RecommendParamDBO;
import com.star.easyfun.content.pojo.dto.ContentPostDTO;
import com.star.easyfun.content.pojo.dto.recommend.RecommendPostDTO;
import com.star.easyfun.content.pojo.dto.recommend.RecommendPostListDTO;
import com.star.easyfun.content.pojo.dto.recommend.RecommendRequestDTO;
import com.star.easyfun.content.pojo.dto.recommend.RecommendTagDTO;
import com.star.easyfun.content.pojo.mapper.PostStructMapper;
import com.star.easyfun.content.service.MinioService;
import com.star.easyfun.content.service.RecommendService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 4月 19 14:15
 */

@Service
@RequiredArgsConstructor
public class RecommendServiceImpl implements RecommendService {

    private final MinioService minioService;
    private final ContentPostMapper postMapper;
    private final ContentInteractionRecordMapper interactionMapper;
    private final RecommendParamMapper recommendParamMapper;
    private final RecommendClient recommendClient;
    private final RedisTemplate<String, Object> redisTemplate;
    private final PostStructMapper postStructMapper;
    private final ObjectMapper jacksonObjectMapper;

    @Override
    public List<ContentPostDTO> getRecommendPostList(Long userId, Integer pageSize) throws JsonProcessingException {
        // 判断冷启动
        String coldStartKey = RedisKeyConstant.getRecommendColdStartCountKey(userId);
        Integer coldStartCount = (Integer) redisTemplate.opsForValue().get(coldStartKey);
        if (coldStartCount == null) {
            coldStartCount = 0;
        }
        redisTemplate.opsForValue().set(coldStartKey, coldStartCount + 1);
        Boolean isColdStart = coldStartCount < 10;
        // 发送OpenFeign请求
        // 处理返回结果并返回
        // TODO: 应将此处直接携带投稿列表和交互信息的写法，改为由推荐模块单独向Java端获取。
        List<ContentPostDBO> postList = getAllPost();
        List<ContentInteractionRecordDBO> interactionList = getAllInteractionRecord();
        List<RecommendTagDTO> userTagList = isColdStart ? getUserTagList(userId) : List.of();
        RecommendRequestDTO requestDTO = new RecommendRequestDTO(postList, interactionList, userTagList);
        RecommendParamDBO recommendParamDBO = getUserRecommendParam(userId);
        if(recommendParamDBO == null){
            recommendParamDBO = new RecommendParamDBO(null, userId, 0.55f, 0.1f, 0.15f);
        }
        RecommendPostListDTO recommendPostList = recommendClient.getRecommendPostList(
                userId,
                isColdStart, pageSize, recommendParamDBO.getAlpha(),
                recommendParamDBO.getWDiv(),
                recommendParamDBO.getWBound(),
                requestDTO);
        List<Long> postIdList = recommendPostList.getRecommendPostList().stream()
                .map(RecommendPostDTO::getPostId).toList();
        return postMapper.selectByIds(postIdList).stream()
                .map(postDBO -> {
                    ContentPostDTO postDTO = postStructMapper.fromPostDBO(postDBO);
                    try {
                        postDTO.setCoverUrl(minioService.getPresignedGetUrl(postDBO.getCoverKey()));
                        return postDTO;
                    }
                    catch (Exception e) {
                        throw new RuntimeException("获取封面Url失败", e);
                    }
                }).toList();
    }

    @Override
    public List<ContentPostDBO> getAllPost() {
        return postMapper.selectList(null);
    }

    @Override
    public List<ContentInteractionRecordDBO> getAllInteractionRecord() {
        return interactionMapper.selectList(null);
    }

    @Override
    public List<RecommendTagDTO> getAllTagList() {
        return recommendClient.getColdStartTagList(50);
    }

    @Override
    public void registerUserTagList(Long userId, List<RecommendTagDTO> tagList) throws JsonProcessingException {
        // Redis缓存用户初始标签列表
        String key = RedisKeyConstant.getContentUserTagListKey(userId);
        redisTemplate.opsForValue().set(key, jacksonObjectMapper.writeValueAsString(tagList));
    }

    @Override
    public List<RecommendTagDTO> getUserTagList(Long userId) throws JsonProcessingException {
        String key = RedisKeyConstant.getContentUserTagListKey(userId);
        Object tagListObj = redisTemplate.opsForValue().get(key);
        if (tagListObj == null) {
            return List.of();
        }
        return jacksonObjectMapper.readValue(tagListObj.toString(), new TypeReference<>() {
        });
    }

    @Override
    public void updateUserRecommendParam(RecommendParamDBO recommendParamDBO) {
        RecommendParamDBO temp = recommendParamMapper.selectOne(new LambdaQueryWrapper<RecommendParamDBO>()
                .eq(RecommendParamDBO::getUserId, recommendParamDBO.getUserId())
        );
        if (temp == null) {
            recommendParamMapper.insert(recommendParamDBO);
        }
        else {
            recommendParamMapper.update(recommendParamDBO, new LambdaUpdateWrapper<RecommendParamDBO>()
                    .eq(RecommendParamDBO::getUserId, recommendParamDBO.getUserId())
            );
        }
    }

    @Override
    public RecommendParamDBO getUserRecommendParam(Long userId) {
        return recommendParamMapper.selectOne(new LambdaQueryWrapper<RecommendParamDBO>()
                .eq(RecommendParamDBO::getUserId, userId)
        );
    }
}