async def scan_create_tasks(self, folder_path):
        """扫描文件夹并创建新任务"""
        try:
            tasks_to_create = []
            for file_path in scan_files(folder_path):
                file_md5 = await self.calc_md5(file_path)
                if not file_md5:
                    logger.warning(f"文件 {file_path} 的MD5计算失败，跳过该文件")
                    continue
                        
                existing_task = (await self.db_session.execute(
                    select(Task).filter_by(uuid=file_md5)  # 在此处使用uuid
                )).scalar_one_or_none()

                if not existing_task:
                    task_type = self.get_task_type(file_path)
                    tasks_to_create.append({
                        'uuid': file_md5,  # 修改此处为uuid
                        'file_name': os.path.basename(file_path),
                        'source': "local" if check_storage_type(file_path) == 'true' else "remote",
                        'file_path': file_path,
                        'md5': file_md5,
                        'cache_path': None,
                        'task_type': task_type
                    })

            for task_data in tasks_to_create:
                try:
                    await self.create_task(**task_data)
                    logger.info(f"为文件 {task_data['file_path']} 创建了新任务")
                except Exception as e:
                    logger.error(f"创建任务失败: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"创建任务时发生错误: {e}", exc_info=True)
            return "fail"
