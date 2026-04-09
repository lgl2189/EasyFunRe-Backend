package com.star.easyfun.user.controller;

import com.star.easyfun.common.constant.CommonRequestHeader;
import com.star.easyfun.common.pojo.dto.Result;
import com.star.easyfun.common.util.ResultUtil;
import com.star.easyfun.user.pojo.dto.UserAllInfoDTO;
import com.star.easyfun.user.pojo.dto.UserPasswordDTO;
import com.star.easyfun.user.pojo.dto.UserPublicInfoDTO;
import com.star.easyfun.user.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 2月 24 15:51
 */

@RestController
@RequestMapping("/account")
@RequiredArgsConstructor
public class AccountController {

    private final UserService userService;

    @GetMapping("/info-all")
    public Result getUserAllInfo(@RequestHeader(CommonRequestHeader.HEADER_USER_ID) String headerUserId) {
        UserAllInfoDTO userAllInfoDTO = userService.getUserAllInfo(headerUserId);
        return ResultUtil.success_10000(userAllInfoDTO, "成功获取用户所有信息");
    }

    @GetMapping("/info-public")
    public Result getUserPublicInfo(@RequestHeader(CommonRequestHeader.HEADER_USER_ID) String headerUserId) {
        UserPublicInfoDTO userPublicInfo = userService.getUserPublicInfo(headerUserId);
        return ResultUtil.success_10000(userPublicInfo, "成功获取用户公开信息");
    }

    @PutMapping("/info-all")
    public Result updateUserAllInfo(@RequestHeader(CommonRequestHeader.HEADER_USER_ID) String headerUserId,
                                    @RequestBody @Validated(UserAllInfoDTO.UpdateInfo.class) UserAllInfoDTO userAllInfoDTO) {
        if (!headerUserId.equals(userAllInfoDTO.getUserId())) {
            return ResultUtil.fail_30000("您没有权限修改此用户信息");
        }
        removeImportantInfo(userAllInfoDTO);
        boolean isSuccess = userService.updateUserAllInfo(userAllInfoDTO);
        if (!isSuccess) {
            return ResultUtil.fail_50000("出现内部错误，修改用户信息失败，请联系客服");
        }
        return ResultUtil.success_10000(userAllInfoDTO, "修改用户信息成功");
    }

    @PutMapping("/password")
    public Result updateUserPassword(@RequestHeader(CommonRequestHeader.HEADER_USER_ID) String headerUserId,
                                     @RequestBody @Validated UserPasswordDTO userPasswordDTO) {
        if (!headerUserId.equals(userPasswordDTO.getUserId())) {
            return ResultUtil.fail_30000("您没有权限修改此用户的密码");
        }
        boolean isSuccess = userService.updateUserPassword(userPasswordDTO);
        if (!isSuccess) {
            return ResultUtil.fail_20005("原密码错误，修改密码失败");
        }
        return ResultUtil.success_10000(LocalDateTime.now(), "密码修改成功");
    }

    private void removeImportantInfo(UserAllInfoDTO userAllInfoDTO) {
        userAllInfoDTO.setPassword(null);
        userAllInfoDTO.setPhone(null);
        userAllInfoDTO.setEmail(null);
    }
}