package com.star.easyfun.user.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.google.common.base.Strings;
import com.star.easyfun.user.mapper.UserBasicMapper;
import com.star.easyfun.user.mapper.UserProfileMapper;
import com.star.easyfun.user.pojo.dbo.UserBasicDBO;
import com.star.easyfun.user.pojo.dbo.UserProfileDBO;
import com.star.easyfun.user.pojo.dto.UserAllInfoDTO;
import com.star.easyfun.user.pojo.dto.UserPasswordDTO;
import com.star.easyfun.user.pojo.dto.UserPublicInfoDTO;
import com.star.easyfun.user.pojo.mapper.UserStructMapper;
import com.star.easyfun.user.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

/**
 * 存储用户的个人信息，包括昵称、头像、简介等扩展信息服务接口实现
 *
 * @author Star
 * @description
 * @since 2026-02-24 14:47:13
 */
@Slf4j
@RequiredArgsConstructor
@Service
public class UserServiceImpl extends ServiceImpl<UserBasicMapper, UserBasicDBO> implements UserService {
    private final UserBasicMapper userBasicMapper;
    private final UserProfileMapper userProfileMapper;
    private final UserStructMapper userStructMapper;
    private final PasswordEncoder passwordEncoder;

    @Override
    public UserAllInfoDTO getUserAllInfo(String userId) {
        UserBasicDBO userBasicDBO = userBasicMapper.selectById(userId);
        LambdaQueryWrapper<UserProfileDBO> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(UserProfileDBO::getUserId, userId);
        UserProfileDBO userProfileDBO = userProfileMapper.selectOne(queryWrapper);
        UserAllInfoDTO userAllInfoDTO = userStructMapper.fromUserDBOUnit(userBasicDBO, userProfileDBO);
        return getSafeUserAllInfo(userAllInfoDTO);
    }

    @Override
    public UserPublicInfoDTO getUserPublicInfo(String userId) {
        LambdaQueryWrapper<UserProfileDBO> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(UserProfileDBO::getUserId, userId);
        UserProfileDBO userProfileDBO = userProfileMapper.selectOne(queryWrapper);
        return userStructMapper.fromUserProfileDBO(userProfileDBO);
    }

    @Override
    public boolean updateUserAllInfo(UserAllInfoDTO userAllInfoDTO) {
        UserBasicDBO userBasicDBO = userStructMapper.fromUserAllInfoDTOToBasicDBO(userAllInfoDTO);
        UserProfileDBO userProfileDBO = userStructMapper.fromUserAllInfoDTOToProfileDBO(userAllInfoDTO);
        userBasicMapper.updateById(userBasicDBO);
        LambdaQueryWrapper<UserProfileDBO> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(UserProfileDBO::getUserId, userAllInfoDTO.getUserId());
        boolean hasProfile = userProfileMapper.selectOne(queryWrapper) != null;
        if (hasProfile) {
            int update = userProfileMapper.update(userProfileDBO, queryWrapper);
            return update == 1;
        }
        else {
            return userProfileMapper.insert(userProfileDBO) == 1;
        }
    }

    @Override
    public boolean updateUserPassword(UserPasswordDTO userPasswordDTO) {
        UserBasicDBO oldBasicDBO = userBasicMapper.selectById(userPasswordDTO.getUserId());
        if (oldBasicDBO == null) {
            return false;
        }
        Long userId = Long.valueOf(userPasswordDTO.getUserId());
        String encodedNewPassword = passwordEncoder.encode(userPasswordDTO.getNewPassword());
        boolean canUpdate = false;
        if (userPasswordDTO.getOldPassword() == null && oldBasicDBO.getPassword() == null) {
            // 用户当前未设置密码
            canUpdate = true;
        }
        else if (!Strings.isNullOrEmpty(userPasswordDTO.getOldPassword()) && passwordEncoder.matches(userPasswordDTO.getOldPassword(), oldBasicDBO.getPassword())) {
            // 用户有密码且密码正确
            canUpdate = true;
        }
        if (canUpdate) {
            UserBasicDBO newUserBasicDBO = new UserBasicDBO()
                    .setUserId(userId)
                    .setPassword(encodedNewPassword);
            userBasicMapper.updateById(newUserBasicDBO);
            return true;
        }
        return false;
    }

    private UserAllInfoDTO getSafeUserAllInfo(UserAllInfoDTO userAllInfoDTO) {
        if (userAllInfoDTO.getPassword() != null) {
            userAllInfoDTO.setPassword("******");
        }
        return userAllInfoDTO;
    }
}