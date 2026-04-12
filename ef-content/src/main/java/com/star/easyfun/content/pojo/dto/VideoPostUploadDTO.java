package com.star.easyfun.content.pojo.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;
import org.hibernate.validator.constraints.Length;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * @author ：Star
 * @description ：    存储一个视频投稿
 * @date ：2026 4月 08 21:34
 */

@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
public class VideoPostUploadDTO {

    /**
     * 投稿标题 -> 对应post表title：VARCHAR(255) 非空
     */
    @NotBlank(message = "投稿标题不能为空", groups = VideoPost.class)
    @Length(max = 255, message = "投稿标题长度不能超过255个字符", groups = VideoPost.class)
    private String postTitle;

    /**
     * 投稿描述 -> 对应post表description：VARCHAR(1000)
     */
    @Length(max = 1000, message = "投稿简介长度不能超过1000个字符", groups = VideoPost.class)
    private String postDescription;

    /**
     * 分p视频标题列表 -> 每个标题对应asset表title：VARCHAR(255) 非空
     * 不分p=1个，分p=多个，至少1个
     */
    @Valid
    @NotEmpty(message = "视资源标题列表不能为空", groups = VideoPost.class)
    @Size(min = 1, message = "资源标题至少填写一个", groups = VideoPost.class)
    private List<@NotBlank(message = "资源标题不能为空", groups = VideoPost.class)
    @Length(max = 255, message = "资源标题不能超过255个字符", groups = VideoPost.class)
            String> videoTitleList;

    /**
     * 是否分p
     */
    private Boolean isMultiPart;

    /**
     * 视频文件列表 -> 1个视频对应1个asset，asset_type=1(视频)
     * 非空；不分p=1个，分p≥1个
     */
    @Valid
    @NotEmpty(message = "视频文件列表不能为空", groups = VideoPost.class)
    @Size(min = 1, message = "至少上传一个视频文件", groups = VideoPost.class)
    private List<@NotNull(message = "视频文件不能为null", groups = VideoPost.class) MultipartFile> videoList;

    /**
     * 封面文件 -> 需求指定忽略校验
     */
    @Valid
    @NotEmpty(message = "视频封面列表不能为空", groups = VideoPost.class)
    @Size(min = 1, max = 1, message = "至少上传一个视频文件", groups = VideoPost.class)
    private List<MultipartFile> coverList;

    /**
     * 视频投稿分组校验标识
     */
    public interface VideoPost {
    }
}