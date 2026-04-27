package com.star.easyfun.content.pojo.mapper;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.star.easyfun.content.pojo.dbo.ContentPostDBO;
import com.star.easyfun.content.pojo.dto.ContentPostDTO;
import com.star.easyfun.content.pojo.dto.ContentPostListDTO;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

/**
 * @author ：Star
 * @description ：    与UserBasicDBO有关的数据转换
 * @date ：2026 3月 06 17:17
 */

@Mapper(componentModel = "spring")
public interface PostStructMapper {
    ContentPostDTO fromPostDBO(ContentPostDBO contentPostDBO);

    @Mapping(source = "records", target = "postList")
    @Mapping(source = "total", target = "total")
    @Mapping(source = "current", target = "current")
    @Mapping(source = "size", target = "size")
    @Mapping(source = "pages", target = "totalPageNum")
    ContentPostListDTO fromPage(IPage<ContentPostDBO> iPage);
}