package com.star.easyfun.content.service.impl;

import com.star.easyfun.content.client.RecommendClient;
import com.star.easyfun.content.constant.RedisKeyConstant;
import com.star.easyfun.content.mapper.ContentInteractionRecordMapper;
import com.star.easyfun.content.mapper.ContentPostMapper;
import com.star.easyfun.content.pojo.dbo.ContentInteractionRecordDBO;
import com.star.easyfun.content.pojo.dbo.ContentPostDBO;
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
    private final RecommendClient recommendClient;
    private final RedisTemplate<String, Object> redisTemplate;
    private final PostStructMapper postStructMapper;

    @Override
    public List<ContentPostDTO> getRecommendPostList(Long userId, Integer pageSize, Float alpha, Float wDiv, Float wBound) {
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
        List<ContentPostDBO> postList = getAllPost();
        List<ContentInteractionRecordDBO> interactionList = getAllInteractionRecord();
        RecommendRequestDTO requestDTO = new RecommendRequestDTO(postList, interactionList);
        RecommendPostListDTO recommendPostList = recommendClient.getRecommendPostList(userId, isColdStart, pageSize, alpha, wDiv, wBound, requestDTO);
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
    public List<RecommendTagDTO> getTagList() {
        return recommendClient.getColdStartTagList(50);
    }


}