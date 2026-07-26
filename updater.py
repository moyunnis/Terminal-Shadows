#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
from datetime import datetime

class SimpleUpdater:
    def __init__(self):
        self.repo_url = "https://github.com/moyunnis/Terminal-Shadows.git"
        self.game_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.expanduser("~/.terminal_shadows")
        self.backup_dir = os.path.join(self.data_dir, "backups")
        self.temp_dir = os.path.join(self.game_dir, "temp_update")
        self.current_version = self.get_current_version()
        
    def get_current_version(self):
        version_file = os.path.join(self.game_dir, "version.txt")
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                return f.read().strip()
        return "5.0"
    
    def check_git_installed(self):
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            return True
        except:
            return False
    
    def create_backup(self):
        print("Создание резервной копии...")
        
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"backup_{timestamp}.zip")
        
        try:
            import zipfile
            saves_dir = os.path.join(self.data_dir, "saves")
            
            with zipfile.ZipFile(backup_file, 'w') as zipf:
                if os.path.exists(saves_dir):
                    for root, dirs, files in os.walk(saves_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.data_dir)
                            zipf.write(file_path, arcname)
                
                config_file = os.path.join(self.data_dir, "config.json")
                if os.path.exists(config_file):
                    zipf.write(config_file, "config.json")
                    
            print(f"Резервная копия создана: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"Ошибка создания резервной копии: {e}")
            return None
    
    def clone_repo(self):
        print("Клонирование репозитория...")
        
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            
            result = subprocess.run([
                "git", "clone", self.repo_url, self.temp_dir
            ], capture_output=True, text=True, check=True)
            
            print("Репозиторий склонирован")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Ошибка клонирования: {e}")
            if e.stderr and "could not resolve host" in e.stderr.lower():
                print("Проверь подключение к интернету.")
            return False
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return False
    
    def get_remote_version(self):
        try:
            version_path = os.path.join(self.temp_dir, "version.txt")
            if os.path.exists(version_path):
                with open(version_path, 'r') as f:
                    return f.read().strip()
            return "unknown"
        except:
            return "unknown"
    
    def update_files(self):
        print("Обновление файлов...")
        
        try:
            update_items = [
                "main.py", "updater.py", "requirements.txt", "version.txt",
                "run_game.sh", "install.sh", "update_game.sh",
                "run_game.bat", "install.bat", "update_game.bat",
                "README.md", "data", "story"
            ]
            
            updated_count = 0
            
            for item in update_items:
                src_path = os.path.join(self.temp_dir, item)
                dst_path = os.path.join(self.game_dir, item)
                
                if os.path.exists(src_path):
                    if os.path.isdir(src_path):
                        if os.path.exists(dst_path):
                            shutil.rmtree(dst_path)
                        shutil.copytree(src_path, dst_path)
                    else:
                        shutil.copy2(src_path, dst_path)
                    
                    print(f"Обновлен: {item}")
                    updated_count += 1
            
            print(f"Обновлено файлов: {updated_count}")
            return True
            
        except Exception as e:
            print(f"Ошибка обновления файлов: {e}")
            return False
    
    def update_dependencies(self):
        print("Обновление зависимостей...")
        
        requirements_file = os.path.join(self.game_dir, "requirements.txt")
        if os.path.exists(requirements_file):
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", 
                    requirements_file, "--upgrade", "--quiet"
                ], check=True)
                print("Зависимости обновлены")
            except Exception as e:
                print(f"Предупреждение: {e}")
        else:
            print("Файл requirements.txt не найден")
    
    def cleanup(self):
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
    
    def run(self):
        print("Обновление Terminal Shadows")
        print("=" * 40)
        print(f"Текущая версия: {self.current_version}")
        print(f"Репозиторий: {self.repo_url}")
        print()
        
        if not self.check_git_installed():
            print("Git не установлен!")
            print("Установите git:")
            print("  Linux: sudo apt install git")
            return
        
        choice = input("Проверить обновления? (y/N): ").strip().lower()
        if choice != 'y':
            print("Проверка отменена")
            return
        
        backup_file = self.create_backup()
        
        if not self.clone_repo():
            self.cleanup()
            return
        
        remote_version = self.get_remote_version()
        print(f"Версия в репозитории: {remote_version}")
        
        if remote_version == self.current_version:
            print("У вас актуальная версия игры!")
            self.cleanup()
            return
        
        choice = input(f"Обновить с {self.current_version} на {remote_version}? (y/N): ").strip().lower()
        if choice != 'y':
            print("Обновление отменено")
            self.cleanup()
            return
        
        if self.update_files():
            self.update_dependencies()
            print("\nОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
            print(f"Резервная копия: {backup_file}")
            print("Перезапустите игру для применения изменений")
        else:
            print("Обновление не удалось")
        
        self.cleanup()

if __name__ == "__main__":
    updater = SimpleUpdater()
    updater.run()
