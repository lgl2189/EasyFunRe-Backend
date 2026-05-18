package com.star.easyfun.content.pojo.dto.recommend;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.util.List;
import java.util.Map;

/**
 * 推荐结果响应DTO
 * 与 Python 端 RecommendResponse 保持字段一致
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
public class RecommendPostListDTO {

    private Long userId;
    private List<RecommendPostDTO> recommendPostList;
    private Boolean isColdStart;
    private String message;

    /**
     * Python 端新增的实验指标（ILD、Novelty 等）
     */
    private Map<String, Object> experimentMetrics;

    /**
     * 实际使用的推荐参数
     */
    private Map<String, Object> actualParams;

    /**
     * 调试信息
     */
    private Map<String, Object> debugQueryParams;

    /**
     * 额外调试信息（如果有）
     */
    private Map<String, Object> debugRequestBody;
}