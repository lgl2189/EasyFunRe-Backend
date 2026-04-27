package com.star.easyfun.content.service;

import com.star.easyfun.content.pojo.dbo.ContentInteractionRecordDBO;
import com.star.easyfun.content.pojo.dbo.ContentPostDBO;
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
     * @param alpha    推荐系统的alpha参数
     * @param wDiv     推荐系统的wDiv参数
     * @param wBound   推荐系统的wBound的参数
     * @return 推荐投稿列表
     */
    List<ContentPostDTO> getRecommendPostList(Long userId, Integer pageSize, Float alpha, Float wDiv, Float wBound);

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
     * @return 冷启动标签列表
     */
    List<RecommendTagDTO> getTagList();
}
