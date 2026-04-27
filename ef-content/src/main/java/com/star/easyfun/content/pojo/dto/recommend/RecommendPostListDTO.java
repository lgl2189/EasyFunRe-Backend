package com.star.easyfun.content.pojo.dto.recommend;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.util.List;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 4月 19 14:06
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
}