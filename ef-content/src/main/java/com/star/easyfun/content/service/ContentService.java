package com.star.easyfun.content.service;

import com.star.easyfun.content.pojo.dto.ContentPostDTO;
import com.star.easyfun.content.pojo.dto.ContentPostListDTO;
import com.star.easyfun.content.pojo.dto.VideoPostUploadDTO;

import java.util.List;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 4月 09 13:11
 */


public interface ContentService {
    /**
     * 完整视频投稿发布
     * @return 新生成的 postId
     */
    Long uploadVideoPost(VideoPostUploadDTO dto, Long ownerId);

    /**
     * 获取投稿的所有信息
     *
     * @param postId 投稿id
     * @param userId 用户id
     * @return 投稿信息
     */
    ContentPostDTO getPost(Long postId, Long userId) throws Exception;

    /**
     * 记录用户浏览投稿
     *
     * @param postId 投稿id
     * @param userId 用户id
     * @return 是否成功
     */
    boolean recordBrowsePost(Long postId, Long userId);

    /**
     * 用户点赞或取消点赞
     * @param postId 投稿id
     * @param userId 用户id
     * @param isLike 点赞或取消点赞，true 点赞，false 取消点赞
     * @return 是否成功
     */
    boolean updatePostLike(Long postId, Long userId, boolean isLike);

    /**
     * 用户点踩或取消点踩
     * @param postId 投稿id
     * @param userId 用户id
     * @param isDislike 点踩或取消点踩，true 点踩，false 取消点踩
     * @return 是否成功
     */
    boolean updatePostDislike(Long postId, Long userId, boolean isDislike);

    /**
     * 根据多个关键字，分页查询投稿列表
     * @param keywordList 关键字列表
     * @param pageNum 页码
     * @param pageSize 每页数量
     * @return 投稿列表
     */
    ContentPostListDTO searchPost(List<String> keywordList, Integer pageNum, Integer pageSize);
}
