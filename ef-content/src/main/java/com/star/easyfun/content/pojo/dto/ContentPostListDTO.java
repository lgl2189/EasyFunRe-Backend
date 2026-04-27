package com.star.easyfun.content.pojo.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.util.List;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 4月 19 11:14
 */

@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
public class ContentPostListDTO {
    private List<ContentPostDTO> postList;
    private Long total;
    private Integer current;
    private Integer size;
    private Integer totalPageNum;
}