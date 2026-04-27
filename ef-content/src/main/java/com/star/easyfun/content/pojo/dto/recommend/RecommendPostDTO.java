package com.star.easyfun.content.pojo.dto.recommend;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 4月 19 14:04
 */

@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
public class RecommendPostDTO {
    private Long postId;
    private Float finalScore;
    private Float HybridScore;
    private String reason;
}