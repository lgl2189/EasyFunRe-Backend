package com.star.easyfun.content.service;

import com.star.easyfun.content.pojo.dto.VideoPostDTO;

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
    Long uploadVideoPost(VideoPostDTO dto, Long ownerId);
}
