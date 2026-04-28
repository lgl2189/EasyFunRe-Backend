package com.star.easyfun.content.constant;

/**
 * @author ：Star
 * @description ：    存储内容服务中Redis用到的键
 * @date ：2026 4月 15 16:12
 */


public class RedisKeyConstant {

    private static final String CACHE_CONTENT_POST_LIKE_RECORD = "cache:content:like";
    private static final String CACHE_CONTENT_POST_BROSE = "cache:content:browse";
    private static final String RECOMMEND_COLD_START_COUNT = "recommend:cold:start:count";
    private static final String CONTENT_USER_TAG_LIST = "content:tag:list";

    public static String getContentCachePostLikeKey(Long postId, Long userId) {
        return CACHE_CONTENT_POST_LIKE_RECORD + ":" + postId + ":" + userId;
    }

    public static String getContentCachePostBrowseKey(Long postId, Long userId) {
        return CACHE_CONTENT_POST_BROSE + ":" + postId + ":" + userId;
    }

    public static String getRecommendColdStartCountKey(Long userId) {
        return RECOMMEND_COLD_START_COUNT + ":" + userId;
    }

    public static String getContentUserTagListKey(Long userId) {
        return CONTENT_USER_TAG_LIST + ":" + userId;
    }

}