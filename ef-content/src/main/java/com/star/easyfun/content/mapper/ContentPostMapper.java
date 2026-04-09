package com.star.easyfun.content.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.star.easyfun.content.pojo.dbo.ContentPost;
import org.apache.ibatis.annotations.Mapper;

/**
 * 投稿信息表 - 存储一个投稿本身的信息(content_post)数据Mapper
 *
 * @author Star
 * @since 2026-04-08 21:08:39
 * @description 
*/
@Mapper
public interface ContentPostMapper extends BaseMapper<ContentPost> {

}
