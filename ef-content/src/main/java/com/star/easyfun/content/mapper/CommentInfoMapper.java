package com.star.easyfun.content.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.star.easyfun.content.pojo.dbo.CommentInfoDBO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 评论表 - 存储一条评论的信息(comment_info)数据Mapper
 *
 * @author Star
 * @since 2026-04-08 21:08:39
 * @description 
*/
@Mapper
public interface CommentInfoMapper extends BaseMapper<CommentInfoDBO> {

}
