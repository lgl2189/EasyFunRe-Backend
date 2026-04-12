package com.star.easyfun.content.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.star.easyfun.content.pojo.dbo.ContentPostResourceDBO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 投稿内容项表 - 存储一个投稿中有哪些内容的信息(content_post_resource)数据Mapper
 *
 * @author Star
 * @since 2026-04-08 21:08:39
 * @description 
*/
@Mapper
public interface ContentPostResourceMapper extends BaseMapper<ContentPostResourceDBO> {

}
