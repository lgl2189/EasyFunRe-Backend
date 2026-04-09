package com.star.easyfun.content.pojo.dbo;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.io.Serial;
import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 内容信息表 - 存储一个资源本身的信息(content_asset)实体类
 *
 * @author Star
 * @since 2026-04-08 21:08:39
 * @description 
 */
@Data
@NoArgsConstructor
@Accessors(chain = true)
@TableName("content_asset")
public class ContentAsset implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 内容的唯一标识，自增主键
     */
    @TableId
	private Long assetId;
    /**
     * 内容类型：1=视频，2=图片，3=音频，4=文本，5=其他
     */
    private Integer assetType;
    /**
     * 内容的标题
     */
    private String title;
    /**
     * 内容的简介
     */
    private String description;
    /**
     * 云存储原始key
     */
    private String fileKey;
    /**
     * 文件大小，单位为字节
     */
    private Long fileSize;
    /**
     * 时长，仅视频、音频有效（单位：秒）
     */
    private Integer duration;
    /**
     * 图片宽度，仅图片有效
     */
    private Integer width;
    /**
     * 图片高度，仅图片有效
     */
    private Integer height;
    /**
     * 内容对应的文件本身的类型
     */
    private String fileType;
    /**
     * 内容状态：1=正常，0=已删除
     */
    private Integer status;
    /**
     * 内容拥有者的ID，即上传者
     */
    private Long ownerId;
    /**
     * 内容的创建时间
     */
    private LocalDateTime createdDatetime;
    /**
     * 内容的更新时间（需手动维护）
     */
    private LocalDateTime updatedDatetime;

}