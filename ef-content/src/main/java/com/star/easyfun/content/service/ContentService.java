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
}
