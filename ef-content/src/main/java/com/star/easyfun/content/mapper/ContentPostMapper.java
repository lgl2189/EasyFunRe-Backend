package com.star.easyfun.content.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.star.easyfun.content.pojo.dbo.ContentPostDBO;
import com.star.easyfun.content.pojo.dto.ContentResourceDTO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * 投稿信息表 - 存储一个投稿本身的信息(content_post)数据Mapper
 *
 * @author Star
 * @since 2026-04-08 21:08:39
 * @description 
*/
@Mapper
public interface ContentPostMapper extends BaseMapper<ContentPostDBO>{
    List<ContentResourceDTO> selectResourceList(Long postId);
}
