package com.star.easyfun.content.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.star.easyfun.content.pojo.dbo.ContentInteractionRecordDBO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 存储用户与投稿内容进行的互动记录(content_interaction_record)数据Mapper
 *
 * @author Star
 * @since 2026-04-12 14:34:30
 * @description 
*/
@Mapper
public interface ContentInteractionRecordMapper extends BaseMapper<ContentInteractionRecordDBO> {

}
