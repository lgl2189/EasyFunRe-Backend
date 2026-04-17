package com.star.easyfun.content.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.ThreadPoolExecutor;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 4月 15 15:15
 */


@Configuration
public class ThreadPoolConfig {

    /**
     * 视频点赞专用异步线程池
     */
    @Bean("contentThreadPool") // 指定bean名称，@Async可指定使用
    public ThreadPoolTaskExecutor contentThreadPool() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();

        // ========== 核心参数（根据你的微服务调整）==========
        executor.setCorePoolSize(10);        // 核心线程数（一直存活）
        executor.setMaxPoolSize(20);         // 最大线程数
        executor.setQueueCapacity(100);      // 阻塞队列容量
        executor.setKeepAliveSeconds(60);    // 非核心线程空闲存活时间
        executor.setThreadNamePrefix("content-async-"); // 线程名前缀（方便日志排查）

        // ========== 拒绝策略（关键！）==========
        // CallerRunsPolicy：队列满了，由调用线程（主线程）执行，保证不丢任务
        // AbortPolicy：队列满了，抛异常，阻止程序运行
        // DiscardPolicy：队列满了，丢弃请求
        // DiscardOldestPolicy：队列满了，丢弃最老的请求
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());

        // 初始化
        executor.initialize();
        return executor;
    }
}