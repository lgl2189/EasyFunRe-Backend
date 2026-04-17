package com.star.easyfun.content.service;

import com.star.easyfun.content.pojo.dto.ContentPostDTO;
import com.star.easyfun.content.pojo.dto.VideoPostUploadDTO;

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
     * @param postId 投稿id
     * @return 投稿信息
     */
    ContentPostDTO getPost(Long postId) throws Exception;

    /**
     * 用户点赞或取消点赞
     * @param postId 投稿id
     * @param userId 用户id
     * @param isLike 点赞或取消点赞，true 点赞，false 取消点赞
     * @return 是否成功
     */
    boolean updatePostLike(Long postId, Long userId, boolean isLike);
}
