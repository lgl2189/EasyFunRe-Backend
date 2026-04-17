package com.star.easyfun.content.service.impl;

import com.star.easyfun.content.service.BehaviorRecordAsyncService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 4月 15 15:22
 */

@Service
@RequiredArgsConstructor
public class BehaviorRecordAsyncServiceImpl implements BehaviorRecordAsyncService {

    private final RedisTemplate<String, Object> redisTemplate;

//    @Async("contentThreadPool")
//    @Override
//    public void recordUserLike(Long userId, Long postId, boolean isLike) {
//        String key = RedisKeyConstant.getContentCachePostLikeKey(postId, userId);
//        if(isLike){
//            redisTemplate.opsForValue().set(key, 1);
//        }
//        else{
//            redisTemplate.opsForValue().set(key, 0);
//        }
//    }
}