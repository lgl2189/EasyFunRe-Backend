package com.star.easyfun.content.pojo.mapper;

import com.star.easyfun.content.pojo.dbo.ContentPostDBO;
import com.star.easyfun.content.pojo.dto.ContentPostDTO;
import org.mapstruct.Mapper;

/**
 * @author ：Star
 * @description ：    与UserBasicDBO有关的数据转换
 * @date ：2026 3月 06 17:17
 */

@Mapper(componentModel = "spring")
public interface PostStructMapper {
    ContentPostDTO fromPostDBO(ContentPostDBO contentPostDBO);
}