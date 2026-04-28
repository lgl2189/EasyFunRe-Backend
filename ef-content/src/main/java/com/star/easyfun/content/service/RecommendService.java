package com.star.easyfun.content.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.star.easyfun.content.pojo.dbo.ContentInteractionRecordDBO;
import com.star.easyfun.content.pojo.dbo.ContentPostDBO;
import com.star.easyfun.content.pojo.dbo.RecommendParamDBO;
import com.star.easyfun.content.pojo.dto.ContentPostDTO;
import com.star.easyfun.content.pojo.dto.recommend.RecommendTagDTO;

import java.util.List;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 4月 19 14:14
 */


public interface RecommendService {
    /**
     * 获取推荐投稿列表
     *
     * @param userId   用户id
     * @param pageSize 每次推荐的投稿数量
     * @return 推荐投稿列表
     */
    List<ContentPostDTO> getRecommendPostList(Long userId, Integer pageSize) throws JsonProcessingException;

    /**
     * 获取所有投稿列表
     *
     * @return 所有投稿
     */
    List<ContentPostDBO> getAllPost();

    /**
     * 获取所有互动记录
     *
     * @return 所有互动记录
     */
    List<ContentInteractionRecordDBO> getAllInteractionRecord();

    /**
     * 获取冷启动标签列表
     *
     * @return 冷启动标签列表
     */
    List<RecommendTagDTO> getAllTagList();

    /**
     * 注册用户初始标签列表
     *
     * @param userId  用户id
     * @param tagList 初始标签列表
     */
    void registerUserTagList(Long userId, List<RecommendTagDTO> tagList) throws JsonProcessingException;

    /**
     * 获取用户初始标签列表
     *
     * @param userId 用户id
     * @return 用户初始标签列表
     */
    List<RecommendTagDTO> getUserTagList(Long userId) throws JsonProcessingException;

    /**
     * 更新用户推荐参数
     *
     * @param recommendParamDBO 推荐参数对象
     */
    void updateUserRecommendParam(RecommendParamDBO recommendParamDBO);

    /**
     * 获取用户推荐参数
     *
     * @param userId 用户id
     * @return 用户推荐参数
     */
    RecommendParamDBO getUserRecommendParam(Long userId);
}
