package com.star.easyfun.content.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.star.easyfun.content.pojo.dbo.CommentAreaDBO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 评论区表 - 存储一个评论区的信息(comment_area)数据Mapper
 *
 * @author Star
 * @since 2026-04-08 21:08:39
 * @description 
*/
@Mapper
public interface CommentAreaMapper extends BaseMapper<CommentAreaDBO> {

}
