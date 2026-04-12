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

    /**
     * 获取视频投稿的播放地址
     * @param postId 投稿id
     * @return 播放地址
     */
    String getVideoPlayUrl(Long postId) throws Exception;
}
