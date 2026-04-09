package com.star.easyfun.content.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.star.easyfun.content.pojo.dbo.ContentAsset;
import org.apache.ibatis.annotations.Mapper;

/**
 * 内容信息表 - 存储一个资源本身的信息(content_asset)数据Mapper
 *
 * @author Star
 * @since 2026-04-08 21:08:39
 * @description 
*/
@Mapper
public interface ContentAssetMapper extends BaseMapper<ContentAsset> {

}
