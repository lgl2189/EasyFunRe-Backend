package com.star.easyfun.content.pojo.dto.recommend;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

/**
 * @author ：Star
 * @description ：    存储冷启动标签列表
 * @date ：2026 4月 27 15:35
 */

@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
public class RecommendTagDTO {
    private String tagName;
}