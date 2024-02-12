@echo off
title Modifying .opt File
python script_modify_opt.py %1
if errorlevel 1 pause
