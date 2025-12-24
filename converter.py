# -*- coding: utf-8 -*-
"""
APK/AAB/APKS Converter Tool
APK/AAB/APKS 批量转换工具

GitHub: https://github.com/planspieldaxe-commits
Telegram联系: https://t.me/webasp
Telegram频道: https://t.me/webjsp

功能：
1. APK转AAB - 自动识别apk目录下的APK文件，批量转换为AAB
2. AAB转APKS - 自动识别aab目录下的AAB文件，批量转换为APKS
3. 自动生成随机签名（符合Google要求）
4. 支持bundletool所有转换模式
5. APKS/XAPK/APKM转APK - 将拆分安装包转换为普通APK
"""

import os
import sys
import zipfile
import shutil
import subprocess
import tempfile
import random
import string
import json
import struct
import re
from pathlib import Path
from datetime import datetime


class Config:
    """配置类"""
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.apk_dir = self.base_dir / "apk"
        self.aab_dir = self.base_dir / "aab"
        self.apks_dir = self.base_dir / "apks"
        self.apk2_dir = self.base_dir / "apk2"  # APKS/XAPK/APKM转换输出目录
        self.split_apk_dir = self.base_dir / "split_apk"  # 放置待转换的APKS/XAPK/APKM文件
        self.keystore_dir = self.base_dir / "keystore"
        self.tools_dir = self.base_dir / "tools"
        
        # 工具路径
        self.bundletool = self.tools_dir / "bundletool.jar"
        self.aapt2 = self.tools_dir / "android-sdk" / "build-tools" / "35.0.0" / "aapt2.exe"
        self.java_home = self.tools_dir / "jdk-21.0.9+10"
        self.java = self.java_home / "bin" / "java.exe"
        self.keytool = self.java_home / "bin" / "keytool.exe"
        self.jarsigner = self.java_home / "bin" / "jarsigner.exe"
        self.zipalign = self.tools_dir / "android-sdk" / "build-tools" / "35.0.0" / "zipalign.exe"
        
    def validate(self):
        """验证必要的工具是否存在"""
        tools = {
            "bundletool.jar": self.bundletool,
            "aapt2.exe": self.aapt2,
            "java.exe": self.java,
            "keytool.exe": self.keytool,
            "jarsigner.exe": self.jarsigner,
        }
        
        missing = []
        for name, path in tools.items():
            if not path.exists():
                missing.append(f"{name}: {path}")
        
        if missing:
            print("[X] 缺少以下工具:")
            for m in missing:
                print(f"   - {m}")
            return False
        
        print("[OK] 所有工具检测通过")
        return True


class RandomSignatureGenerator:
    """随机签名生成器 - 符合Google Play要求"""
    
    # 常见的英文名字
    FIRST_NAMES = [
        "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
        "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark",
        "Emma", "Olivia", "Ava", "Isabella", "Sophia", "Mia", "Charlotte", "Amelia"
    ]
    
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White"
    ]
    
    # 公司后缀
    COMPANY_SUFFIXES = ["Inc", "LLC", "Corp", "Ltd", "Co", "Technologies", "Software", "Apps", "Mobile", "Digital"]
    
    # 部门名称
    DEPARTMENTS = ["Development", "Engineering", "Mobile", "Android", "Software", "Technology", "Digital", "Apps"]
    
    # 城市
    CITIES = [
        "San Francisco", "New York", "Los Angeles", "Seattle", "Austin", "Boston", 
        "Chicago", "Denver", "Portland", "San Diego", "Atlanta", "Miami",
        "London", "Berlin", "Tokyo", "Singapore", "Sydney", "Toronto"
    ]
    
    # 州/省
    STATES = [
        "California", "New York", "Texas", "Washington", "Massachusetts", "Colorado",
        "Oregon", "Florida", "Georgia", "Illinois", "Virginia", "Arizona"
    ]
    
    # 国家代码
    COUNTRIES = ["US", "GB", "DE", "JP", "SG", "AU", "CA", "FR", "NL", "SE"]
    
    @classmethod
    def generate_password(cls, length=16):
        """生成安全密码（避免使用可能导致命令行问题的特殊字符）"""
        # 只使用字母和数字，避免特殊字符在命令行中的问题
        chars = string.ascii_letters + string.digits
        password = ''.join(random.choice(chars) for _ in range(length))
        return password
    
    @classmethod
    def generate_alias(cls):
        """生成密钥别名"""
        return f"key_{random.randint(10000, 99999)}"
    
    @classmethod
    def generate_dname(cls):
        """生成随机的Distinguished Name（符合Google要求）"""
        # 生成公司名
        first = random.choice(cls.FIRST_NAMES)
        last = random.choice(cls.LAST_NAMES)
        suffix = random.choice(cls.COMPANY_SUFFIXES)
        
        cn = f"{first} {last}"  # Common Name - 开发者名称
        ou = random.choice(cls.DEPARTMENTS)  # Organizational Unit - 部门
        o = f"{last} {suffix}"  # Organization - 组织
        l = random.choice(cls.CITIES)  # Locality - 城市
        st = random.choice(cls.STATES)  # State - 州
        c = random.choice(cls.COUNTRIES)  # Country - 国家
        
        dname = f"CN={cn}, OU={ou}, O={o}, L={l}, ST={st}, C={c}"
        return dname, {
            "cn": cn, "ou": ou, "o": o, "l": l, "st": st, "c": c
        }
    
    @classmethod
    def generate_keystore(cls, keytool_path, output_path, validity_days=10000):
        """
        生成随机keystore文件
        
        Args:
            keytool_path: keytool工具路径
            output_path: keystore输出路径
            validity_days: 有效期天数（Google建议至少25年≈9125天）
        
        Returns:
            dict: 包含keystore信息的字典
        """
        # PKCS12格式要求store密码和key密码相同
        password = cls.generate_password()
        store_password = password
        key_password = password
        alias = cls.generate_alias()
        dname, dname_info = cls.generate_dname()
        
        keystore_file = Path(output_path)
        
        # keytool命令
        cmd = [
            str(keytool_path),
            "-genkeypair",
            "-alias", alias,
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", str(validity_days),
            "-keystore", str(keystore_file),
            "-storepass", store_password,
            "-keypass", key_password,
            "-dname", dname
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            keystore_info = {
                "keystore_file": str(keystore_file),
                "store_password": store_password,
                "key_alias": alias,
                "key_password": key_password,
                "dname": dname,
                "dname_info": dname_info,
                "validity_days": validity_days,
                "created_at": datetime.now().isoformat()
            }
            
            # 保存keystore信息到JSON文件
            info_file = keystore_file.with_suffix('.json')
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(keystore_info, f, indent=2, ensure_ascii=False)
            
            print(f"  [OK] Keystore生成成功: {keystore_file.name}")
            print(f"     别名: {alias}")
            print(f"     DN: {dname}")
            
            return keystore_info
            
        except subprocess.CalledProcessError as e:
            print(f"  [X] Keystore生成失败: {e.stderr}")
            return None


class APKtoAABConverter:
    """APK转AAB转换器 - 使用aapt2 convert方式"""
    
    def __init__(self, config):
        self.config = config
        
    def convert_apk_to_proto(self, apk_path, output_path):
        """
        使用aapt2将APK转换为proto格式
        
        Args:
            apk_path: 输入APK路径
            output_path: 输出proto APK路径
        
        Returns:
            bool: 是否成功
        """
        cmd = [
            str(self.config.aapt2),
            "convert",
            "-o", str(output_path),
            "--output-format", "proto",
            str(apk_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        # aapt2 convert会输出警告但仍然成功
        if result.returncode != 0:
            print(f"  [X] aapt2 convert错误: {result.stderr}")
            return False
        
        return True
    
    def extract_proto_apk(self, proto_apk_path, output_dir):
        """解压proto格式的APK"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(proto_apk_path, 'r') as zf:
            zf.extractall(output_path)
        
        return output_path
    
    def create_base_module(self, extracted_dir, output_dir):
        """
        从proto APK创建base模块目录结构
        
        Proto APK结构已经是:
        - AndroidManifest.xml (proto格式)
        - resources.pb (proto格式的资源表)
        - res/ (资源文件)
        - classes.dex
        - lib/
        - assets/
        
        Bundle模块结构:
        base/
        ├── manifest/AndroidManifest.xml
        ├── dex/classes.dex, classes2.dex, ...
        ├── res/
        ├── lib/
        ├── assets/
        └── root/
        """
        base_dir = Path(output_dir) / "base"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        apk_dir = Path(extracted_dir)
        
        # 1. 创建manifest目录并复制AndroidManifest.xml
        manifest_dir = base_dir / "manifest"
        manifest_dir.mkdir(exist_ok=True)
        
        manifest_src = apk_dir / "AndroidManifest.xml"
        if manifest_src.exists():
            shutil.copy2(manifest_src, manifest_dir / "AndroidManifest.xml")
        
        # 2. 创建dex目录并复制所有dex文件
        dex_dir = base_dir / "dex"
        dex_dir.mkdir(exist_ok=True)
        
        for dex_file in apk_dir.glob("*.dex"):
            shutil.copy2(dex_file, dex_dir / dex_file.name)
        
        # 3. 复制res目录
        res_src = apk_dir / "res"
        if res_src.exists():
            res_dst = base_dir / "res"
            if res_dst.exists():
                shutil.rmtree(res_dst)
            shutil.copytree(res_src, res_dst)
        
        # 4. 复制lib目录（native库）
        lib_src = apk_dir / "lib"
        if lib_src.exists():
            lib_dst = base_dir / "lib"
            if lib_dst.exists():
                shutil.rmtree(lib_dst)
            shutil.copytree(lib_src, lib_dst)
        
        # 5. 复制assets目录
        assets_src = apk_dir / "assets"
        if assets_src.exists():
            assets_dst = base_dir / "assets"
            if assets_dst.exists():
                shutil.rmtree(assets_dst)
            shutil.copytree(assets_src, assets_dst)
        
        # 6. 创建root目录存放其他文件
        root_dir = base_dir / "root"
        root_dir.mkdir(exist_ok=True)
        
        # 复制resources.pb（proto格式的资源表）
        resources_pb = apk_dir / "resources.pb"
        if resources_pb.exists():
            shutil.copy2(resources_pb, base_dir / "resources.pb")
        
        # 已处理的文件/目录
        excluded_items = {
            'AndroidManifest.xml', 'res', 'lib', 'assets', 
            'resources.pb', 'META-INF'
        }
        
        # Bundle保留的文件/目录名（不能在root目录中使用）
        reserved_names = {
            'resources.arsc', 'resources.pb', 'manifest', 
            'dex', 'res', 'lib', 'assets', 'root'
        }
        
        # 复制其他文件到root目录
        for item in apk_dir.iterdir():
            # 跳过已处理的和dex文件
            if item.name in excluded_items or item.name.endswith('.dex'):
                continue
            
            # 处理保留名称 - 重命名
            dst_name = item.name
            if item.name.lower() in reserved_names or item.name in reserved_names:
                dst_name = f"_{item.name}_"
                print(f"  [!] 重命名保留名称: {item.name} -> {dst_name}")
            
            dst_path = root_dir / dst_name
            try:
                if item.is_file():
                    shutil.copy2(item, dst_path)
                elif item.is_dir():
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(item, dst_path)
            except Exception as e:
                print(f"  [!] 复制跳过 {item.name}: {e}")
        
        return base_dir
    
    def create_base_zip(self, base_dir, output_zip):
        """将base模块打包为zip"""
        base_path = Path(base_dir)
        output_path = Path(output_zip)
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in base_path.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(base_path)
                    zf.write(file, arcname)
        
        return output_path
    
    def build_aab(self, base_zip, output_aab):
        """使用bundletool构建AAB"""
        # 如果输出文件已存在，先删除
        output_path = Path(output_aab)
        if output_path.exists():
            output_path.unlink()
            print(f"  [i] 删除已存在的AAB: {output_path.name}")
        
        cmd = [
            str(self.config.java),
            "-jar", str(self.config.bundletool),
            "build-bundle",
            f"--modules={base_zip}",
            f"--output={output_aab}"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  [X] bundletool错误: {result.stderr}")
            return False
        
        return True
    
    def sign_aab(self, aab_path, keystore_info):
        """使用jarsigner签名AAB"""
        cmd = [
            str(self.config.jarsigner),
            "-verbose",
            "-sigalg", "SHA256withRSA",
            "-digestalg", "SHA-256",
            "-keystore", keystore_info["keystore_file"],
            "-storepass", keystore_info["store_password"],
            "-keypass", keystore_info["key_password"],
            str(aab_path),
            keystore_info["key_alias"]
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  [X] 签名错误: {result.stderr}")
            return False
        
        return True
    
    def get_package_info_from_aapt2(self, apk_path):
        """使用aapt2获取APK包信息"""
        cmd = [
            str(self.config.aapt2),
            "dump", "badging",
            str(apk_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        package_name = ""
        version_code = ""
        version_name = ""
        
        if result.returncode == 0:
            output = result.stdout
            
            # 提取包名
            match = re.search(r"package: name='([^']+)'", output)
            if match:
                package_name = match.group(1)
            
            # 提取版本号
            match = re.search(r"versionCode='(\d+)'", output)
            if match:
                version_code = match.group(1)
            
            # 提取版本名
            match = re.search(r"versionName='([^']+)'", output)
            if match:
                version_name = match.group(1)
        
        return {
            "package_name": package_name,
            "version_code": version_code,
            "version_name": version_name
        }
    
    def convert(self, apk_path, auto_sign=True, output_dir=None):
        """
        完整的APK转AAB转换流程
        
        Args:
            apk_path: APK文件路径
            auto_sign: 是否自动生成签名
            output_dir: 自定义输出目录（可选，默认使用config中的aab_dir）
        
        Returns:
            str: 生成的AAB文件路径，失败返回None
        """
        apk_path = Path(apk_path)
        apk_name = apk_path.stem
        
        # 确定输出目录
        if output_dir:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = self.config.aab_dir
        
        print(f"\n{'='*60}")
        print(f"[*] 开始转换: {apk_path.name}")
        print(f"{'='*60}")
        
        # 获取包信息
        print("\n[1/6] 获取APK信息...")
        pkg_info = self.get_package_info_from_aapt2(apk_path)
        if pkg_info['package_name']:
            print(f"  [i] 包名: {pkg_info['package_name']}")
            print(f"  [i] 版本: {pkg_info['version_name']} ({pkg_info['version_code']})")
        else:
            print("  [!] 无法获取包信息，继续转换...")
        
        # 创建临时工作目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 2. 使用aapt2将APK转换为proto格式
            print("\n[2/6] 转换APK为Proto格式...")
            proto_apk = temp_path / "proto.apk"
            if not self.convert_apk_to_proto(apk_path, proto_apk):
                return None
            print(f"  [OK] Proto APK生成成功")
            
            # 3. 解压proto APK
            print("\n[3/6] 解压Proto APK...")
            extracted_dir = temp_path / "extracted"
            self.extract_proto_apk(proto_apk, extracted_dir)
            print(f"  [OK] 解压完成")
            
            # 4. 创建Bundle模块结构
            print("\n[4/6] 创建Bundle模块结构...")
            module_dir = temp_path / "module"
            base_dir = self.create_base_module(extracted_dir, module_dir)
            print(f"  [OK] 模块结构创建完成")
            
            # 5. 打包为base.zip
            print("\n[5/6] 打包模块并构建AAB...")
            base_zip = temp_path / "base.zip"
            self.create_base_zip(base_dir, base_zip)
            
            # 构建AAB
            output_aab = out_dir / f"{apk_name}.aab"
            
            if not self.build_aab(base_zip, output_aab):
                return None
            print(f"  [OK] AAB构建完成: {output_aab.name}")
            
            # 6. 签名AAB
            if auto_sign:
                print("\n[6/6] 生成签名并签名AAB...")
                
                keystore_path = self.config.keystore_dir / f"{apk_name}.jks"
                keystore_json = self.config.keystore_dir / f"{apk_name}.json"
                
                # 检查是否已存在 keystore
                if keystore_path.exists() and keystore_json.exists():
                    print(f"  [i] 发现已存在的keystore: {keystore_path.name}")
                    with open(keystore_json, 'r', encoding='utf-8') as f:
                        keystore_info = json.load(f)
                    print(f"     别名: {keystore_info.get('key_alias', 'N/A')}")
                else:
                    # 生成随机keystore
                    keystore_info = RandomSignatureGenerator.generate_keystore(
                        self.config.keytool,
                        keystore_path
                    )
                
                if keystore_info:
                    if self.sign_aab(output_aab, keystore_info):
                        print(f"  [OK] AAB签名完成")
                    else:
                        print(f"  [!] AAB签名失败，但AAB文件已生成")
                else:
                    print(f"  [!] Keystore生成失败，AAB未签名")
            else:
                print("\n[6/6] 跳过签名")
        
        print(f"\n[OK] 转换完成: {output_aab}")
        return str(output_aab)


class AABtoAPKSConverter:
    """AAB转APKS转换器 - 支持bundletool所有模式"""
    
    # bundletool支持的所有模式
    MODES = {
        "default": "默认模式 - 生成针对所有设备的拆分APK集合",
        "universal": "通用模式 - 生成包含所有配置的单一通用APK",
        "system": "系统模式 - 生成用于系统镜像的APK",
        "system_compressed": "压缩系统模式 - 生成压缩的系统APK",
        "instant": "即时应用模式 - 生成即时应用APK",
        "persistent": "持久模式 - 生成持久APK",
        "archive": "存档模式 - 生成存档APK"
    }
    
    def __init__(self, config):
        self.config = config
    
    def find_keystore_for_aab(self, aab_name):
        """
        查找AAB对应的keystore文件
        优先查找同名的keystore，否则使用第一个可用的keystore
        """
        # 尝试查找同名的keystore
        keystore_json = self.config.keystore_dir / f"{aab_name}.json"
        if keystore_json.exists():
            with open(keystore_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 查找任意可用的keystore
        for json_file in self.config.keystore_dir.glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                info = json.load(f)
                keystore_path = Path(info.get("keystore_file", ""))
                if keystore_path.exists():
                    print(f"  [!] 使用keystore: {keystore_path.name}")
                    return info
        
        return None
    
    def build_apks(self, aab_path, output_path, keystore_info=None, mode="default", 
                   device_spec=None, local_testing=False, verbose=False):
        """
        使用bundletool将AAB转换为APKS
        
        Args:
            aab_path: AAB文件路径
            output_path: 输出APKS路径
            keystore_info: keystore信息字典
            mode: 转换模式 (default/universal/system/instant/persistent/archive)
            device_spec: 设备规格JSON文件路径（可选）
            local_testing: 是否启用本地测试模式
            verbose: 是否显示详细信息
        
        Returns:
            bool: 是否成功
        """
        cmd = [
            str(self.config.java),
            "-jar", str(self.config.bundletool),
            "build-apks",
            f"--bundle={aab_path}",
            f"--output={output_path}",
            "--overwrite"
        ]
        
        # 添加模式
        if mode and mode != "default":
            cmd.append(f"--mode={mode}")
        
        # 添加设备规格
        if device_spec:
            cmd.append(f"--device-spec={device_spec}")
        
        # 添加本地测试模式
        if local_testing:
            cmd.append("--local-testing")
        
        # 添加详细输出
        if verbose:
            cmd.append("--verbose")
        
        # 添加aapt2路径
        cmd.append(f"--aapt2={self.config.aapt2}")
        
        # 添加签名信息
        if keystore_info:
            cmd.extend([
                f"--ks={keystore_info['keystore_file']}",
                f"--ks-pass=pass:{keystore_info['store_password']}",
                f"--ks-key-alias={keystore_info['key_alias']}",
                f"--key-pass=pass:{keystore_info['key_password']}"
            ])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  [X] bundletool错误: {result.stderr}")
            return False
        
        if verbose and result.stdout:
            print(result.stdout)
        
        return True
    
    def convert(self, aab_path, mode="default", device_spec=None, 
                local_testing=False, verbose=False, output_dir=None, auto_sign=True):
        """
        完整的AAB转APKS转换流程
        
        Args:
            aab_path: AAB文件路径
            mode: 转换模式
            device_spec: 设备规格文件（可选）
            local_testing: 本地测试模式
            verbose: 详细输出
            output_dir: 自定义输出目录（可选，默认使用config中的apks_dir）
            auto_sign: 是否使用签名（默认True）
        
        Returns:
            str: 生成的APKS文件路径，失败返回None
        """
        aab_path = Path(aab_path)
        aab_name = aab_path.stem
        
        # 确定输出目录
        if output_dir:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = self.config.apks_dir
        
        print(f"\n{'='*60}")
        print(f"[*] 开始转换: {aab_path.name}")
        print(f"    模式: {mode} - {self.MODES.get(mode, '未知模式')}")
        print(f"{'='*60}")
        
        # 1. 查找keystore
        keystore_info = None
        if auto_sign:
            print("\n[1/2] 查找签名文件...")
            keystore_info = self.find_keystore_for_aab(aab_name)
            
            if keystore_info:
                print(f"  [OK] 找到keystore: {Path(keystore_info['keystore_file']).name}")
                print(f"     别名: {keystore_info['key_alias']}")
            else:
                print("  [!] 未找到keystore，APKS将使用debug签名")
        else:
            print("\n[1/2] 跳过签名...")
        
        # 2. 构建APKS
        print(f"\n[2/2] 构建APKS (模式: {mode})...")
        
        # 根据模式确定输出文件名
        if mode == "default":
            output_name = f"{aab_name}.apks"
        else:
            output_name = f"{aab_name}_{mode}.apks"
        
        output_apks = out_dir / output_name
        
        if self.build_apks(
            aab_path, output_apks, keystore_info,
            mode=mode, device_spec=device_spec,
            local_testing=local_testing, verbose=verbose
        ):
            print(f"  [OK] APKS构建完成: {output_apks.name}")
            
            # 显示APKS文件大小
            size_mb = output_apks.stat().st_size / (1024 * 1024)
            print(f"  [i] 文件大小: {size_mb:.2f} MB")
            
            print(f"\n[OK] 转换完成: {output_apks}")
            return str(output_apks)
        else:
            return None
    
    def convert_all_modes(self, aab_path, verbose=False):
        """
        使用所有模式转换AAB到APKS
        
        Args:
            aab_path: AAB文件路径
            verbose: 详细输出
        
        Returns:
            dict: 各模式的转换结果
        """
        results = {}
        
        for mode in self.MODES.keys():
            try:
                result = self.convert(aab_path, mode=mode, verbose=verbose)
                results[mode] = "success" if result else "failed"
            except Exception as e:
                print(f"  [X] {mode}模式转换失败: {e}")
                results[mode] = "failed"
        
        return results


class SplitAPKtoAPKConverter:
    """
    APKS/XAPK/APKM 转 APK 转换器
    
    支持的格式:
    - APKS: bundletool生成的拆分APK集合
    - XAPK: APKPure等第三方商店的格式
    - APKM: APKMirror的格式
    """
    
    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = ['.apks', '.xapk', '.apkm']
    
    def __init__(self, config):
        self.config = config
    
    def detect_format(self, file_path):
        """检测文件格式"""
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        if ext in self.SUPPORTED_EXTENSIONS:
            return ext[1:]  # 去掉点号
        return None
    
    def analyze_archive(self, archive_path):
        """
        分析压缩包内容，确定最佳提取策略
        
        Returns:
            dict: 包含分析结果的字典
        """
        archive_path = Path(archive_path)
        result = {
            "format": self.detect_format(archive_path),
            "has_universal": False,
            "has_standalone": False,
            "base_apk": None,
            "split_apks": [],
            "all_apks": [],
            "manifest": None,
            "obb_files": []
        }
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                file_list = zf.namelist()
                
                for name in file_list:
                    name_lower = name.lower()
                    
                    # 查找APK文件
                    if name_lower.endswith('.apk'):
                        result["all_apks"].append(name)
                        
                        # 检查是否是universal APK
                        if 'universal' in name_lower or 'standalone' in name_lower:
                            result["has_universal"] = True
                            result["base_apk"] = name
                        # 检查base APK
                        elif 'base' in name_lower and 'master' in name_lower:
                            if not result["base_apk"]:
                                result["base_apk"] = name
                        elif name_lower.endswith('base.apk') or name_lower == 'base.apk':
                            if not result["base_apk"]:
                                result["base_apk"] = name
                        # 配置拆分APK
                        elif 'config.' in name_lower or 'split_config' in name_lower:
                            result["split_apks"].append(name)
                        # 其他拆分APK (XAPK格式)
                        elif 'split_' in name_lower:
                            result["split_apks"].append(name)
                    
                    # 查找manifest文件 (XAPK/APKM)
                    if name_lower == 'manifest.json' or name_lower == 'info.json':
                        result["manifest"] = name
                    
                    # 查找OBB文件
                    if name_lower.endswith('.obb'):
                        result["obb_files"].append(name)
                
                # 如果没找到明确的base APK，使用第一个APK
                if not result["base_apk"] and result["all_apks"]:
                    # 优先选择不含config/split的APK
                    for apk in result["all_apks"]:
                        apk_lower = apk.lower()
                        if 'config' not in apk_lower and 'split_' not in apk_lower:
                            result["base_apk"] = apk
                            break
                    # 还是没找到就用第一个
                    if not result["base_apk"]:
                        result["base_apk"] = result["all_apks"][0]
                
        except zipfile.BadZipFile:
            print(f"  [X] 无效的压缩文件: {archive_path.name}")
            return None
        
        return result
    
    def extract_universal_apk(self, archive_path, output_path, analysis, auto_sign=True):
        """提取universal/standalone APK
        
        Args:
            auto_sign: 是否重新签名（对于提取的APK，通常已有签名，此参数保留以备将来使用）
        """
        with zipfile.ZipFile(archive_path, 'r') as zf:
            # 读取universal APK
            apk_data = zf.read(analysis["base_apk"])
            
            # 写入输出文件
            with open(output_path, 'wb') as f:
                f.write(apk_data)
        
        return True
    
    def merge_split_apks(self, archive_path, output_path, analysis, auto_sign=True):
        """
        合并拆分APK为单一APK
        
        策略：
        1. 解压所有APK到临时目录
        2. 合并内容（DEX、资源、库文件等）
        3. 重新打包并签名（如果auto_sign为True）
        
        Args:
            auto_sign: 是否自动签名（默认True）
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            merged_dir = temp_path / "merged"
            merged_dir.mkdir()
            
            apks_to_merge = [analysis["base_apk"]] + analysis["split_apks"]
            
            print(f"  [i] 合并 {len(apks_to_merge)} 个APK文件...")
            
            # 解压所有APK
            with zipfile.ZipFile(archive_path, 'r') as archive:
                for apk_name in apks_to_merge:
                    print(f"     - {Path(apk_name).name}")
                    
                    # 提取APK到临时文件
                    apk_data = archive.read(apk_name)
                    temp_apk = temp_path / Path(apk_name).name
                    with open(temp_apk, 'wb') as f:
                        f.write(apk_data)
                    
                    # 解压APK内容
                    try:
                        with zipfile.ZipFile(temp_apk, 'r') as apk_zip:
                            for item in apk_zip.namelist():
                                # 跳过签名文件
                                if item.startswith('META-INF/'):
                                    continue
                                
                                item_path = merged_dir / item
                                
                                # 如果文件已存在，需要特殊处理
                                if item_path.exists():
                                    # DEX文件需要特殊处理（按编号累加）
                                    if item.endswith('.dex'):
                                        # 找到下一个可用的DEX编号
                                        dex_num = 2
                                        while True:
                                            new_name = f"classes{dex_num}.dex"
                                            new_path = merged_dir / new_name
                                            if not new_path.exists():
                                                item_path = new_path
                                                break
                                            dex_num += 1
                                    else:
                                        # 其他文件跳过（使用base APK的版本）
                                        continue
                                
                                # 创建目录
                                item_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                # 写入文件
                                if not item.endswith('/'):
                                    with open(item_path, 'wb') as f:
                                        f.write(apk_zip.read(item))
                    
                    except zipfile.BadZipFile:
                        print(f"  [!] 跳过无效APK: {Path(apk_name).name}")
                        continue
            
            # 重新打包为APK
            print("  [i] 重新打包APK...")
            temp_output = temp_path / "merged.apk"
            
            with zipfile.ZipFile(temp_output, 'w', zipfile.ZIP_DEFLATED) as out_zip:
                for file in merged_dir.rglob('*'):
                    if file.is_file():
                        arcname = file.relative_to(merged_dir)
                        out_zip.write(file, arcname)
            
            # 对齐APK
            print("  [i] 对齐APK...")
            aligned_apk = temp_path / "aligned.apk"
            
            cmd = [
                str(self.config.zipalign),
                "-f", "-p", "4",
                str(temp_output),
                str(aligned_apk)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"  [!] zipalign警告: {result.stderr}")
                # 即使对齐失败也继续
                aligned_apk = temp_output
            
            # 签名APK
            if auto_sign:
                print("  [i] 签名APK...")
                
                # 查找可用的keystore
                keystore_info = None
                for json_file in self.config.keystore_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                            if Path(info.get("keystore_file", "")).exists():
                                keystore_info = info
                                break
                    except:
                        continue
                
                if keystore_info:
                    # 使用apksigner签名
                    apksigner = self.config.tools_dir / "android-sdk" / "build-tools" / "35.0.0" / "apksigner.bat"
                    
                    if apksigner.exists():
                        signed_apk = temp_path / "signed.apk"
                        cmd = [
                            str(apksigner),
                            "sign",
                            "--ks", keystore_info["keystore_file"],
                            "--ks-pass", f"pass:{keystore_info['store_password']}",
                            "--ks-key-alias", keystore_info["key_alias"],
                            "--key-pass", f"pass:{keystore_info['key_password']}",
                            "--out", str(signed_apk),
                            str(aligned_apk)
                        ]
                        
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            aligned_apk = signed_apk
                            print(f"  [OK] 签名成功")
                        else:
                            print(f"  [!] 签名失败: {result.stderr}")
                    else:
                        # 使用jarsigner
                        cmd = [
                            str(self.config.jarsigner),
                            "-verbose",
                            "-sigalg", "SHA256withRSA",
                            "-digestalg", "SHA-256",
                            "-keystore", keystore_info["keystore_file"],
                            "-storepass", keystore_info["store_password"],
                            "-keypass", keystore_info["key_password"],
                            str(aligned_apk),
                            keystore_info["key_alias"]
                        ]
                        
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            print(f"  [OK] 签名成功")
                        else:
                            print(f"  [!] 签名失败: {result.stderr}")
                else:
                    print("  [!] 未找到keystore，APK未签名")
            else:
                print("  [i] 跳过签名")
            
            # 复制到输出路径
            shutil.copy2(aligned_apk, output_path)
        
        return True
    
    def get_package_info_from_manifest(self, archive_path, manifest_name):
        """从manifest.json或info.json获取包信息"""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                manifest_data = zf.read(manifest_name)
                manifest = json.loads(manifest_data.decode('utf-8'))
                
                return {
                    "package_name": manifest.get("package_name", manifest.get("packageName", "")),
                    "version_code": str(manifest.get("version_code", manifest.get("versionCode", ""))),
                    "version_name": manifest.get("version_name", manifest.get("versionName", "")),
                    "name": manifest.get("name", manifest.get("app_name", ""))
                }
        except:
            return None
    
    def convert(self, input_path, output_dir=None, auto_sign=True):
        """
        转换APKS/XAPK/APKM为普通APK
        
        Args:
            input_path: 输入文件路径
            output_dir: 自定义输出目录（可选，默认使用config中的apk2_dir）
            auto_sign: 是否自动签名（默认True）
        
        Returns:
            str: 生成的APK文件路径，失败返回None
        """
        input_path = Path(input_path)
        file_name = input_path.stem
        
        # 确定输出目录
        if output_dir:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = self.config.apk2_dir
        
        print(f"\n{'='*60}")
        print(f"[*] 开始转换: {input_path.name}")
        print(f"{'='*60}")
        
        # 1. 检测格式
        file_format = self.detect_format(input_path)
        if not file_format:
            print(f"  [X] 不支持的文件格式: {input_path.suffix}")
            return None
        
        print(f"\n[1/4] 检测文件格式...")
        print(f"  [i] 格式: {file_format.upper()}")
        
        # 2. 分析内容
        print(f"\n[2/4] 分析压缩包内容...")
        analysis = self.analyze_archive(input_path)
        
        if not analysis:
            return None
        
        print(f"  [i] 发现 {len(analysis['all_apks'])} 个APK文件")
        
        if analysis["manifest"]:
            pkg_info = self.get_package_info_from_manifest(input_path, analysis["manifest"])
            if pkg_info:
                print(f"  [i] 包名: {pkg_info.get('package_name', 'N/A')}")
                print(f"  [i] 版本: {pkg_info.get('version_name', 'N/A')}")
        
        if analysis["has_universal"]:
            print(f"  [i] 发现Universal/Standalone APK")
        elif analysis["split_apks"]:
            print(f"  [i] 发现 {len(analysis['split_apks'])} 个拆分配置APK")
        
        if analysis["obb_files"]:
            print(f"  [!] 发现 {len(analysis['obb_files'])} 个OBB文件（将被忽略）")
        
        # 3. 确定输出路径
        output_apk = out_dir / f"{file_name}.apk"
        
        # 如果输出文件已存在，先删除
        if output_apk.exists():
            output_apk.unlink()
            print(f"  [i] 删除已存在的APK: {output_apk.name}")
        
        # 4. 执行转换
        print(f"\n[3/4] 提取/合并APK...")
        
        success = False
        
        if analysis["has_universal"]:
            # 直接提取universal APK
            print(f"  [i] 提取: {Path(analysis['base_apk']).name}")
            success = self.extract_universal_apk(input_path, output_apk, analysis, auto_sign)
        elif len(analysis["all_apks"]) == 1:
            # 只有一个APK，直接提取
            print(f"  [i] 提取: {Path(analysis['all_apks'][0]).name}")
            analysis["base_apk"] = analysis["all_apks"][0]
            success = self.extract_universal_apk(input_path, output_apk, analysis, auto_sign)
        elif analysis["base_apk"]:
            # 有拆分APK，需要合并
            if analysis["split_apks"]:
                success = self.merge_split_apks(input_path, output_apk, analysis, auto_sign)
            else:
                # 只有base APK
                print(f"  [i] 提取: {Path(analysis['base_apk']).name}")
                success = self.extract_universal_apk(input_path, output_apk, analysis, auto_sign)
        else:
            print(f"  [X] 无法找到可用的APK文件")
            return None
        
        if not success:
            return None
        
        # 5. 验证输出
        print(f"\n[4/4] 验证输出...")
        
        if output_apk.exists():
            size_mb = output_apk.stat().st_size / (1024 * 1024)
            print(f"  [OK] APK生成成功: {output_apk.name}")
            print(f"  [i] 文件大小: {size_mb:.2f} MB")
            
            print(f"\n[OK] 转换完成: {output_apk}")
            return str(output_apk)
        else:
            print(f"  [X] APK生成失败")
            return None


def batch_convert_split_to_apk(config):
    """批量转换APKS/XAPK/APKM到APK"""
    # 获取所有支持的文件
    all_files = []
    for ext in SplitAPKtoAPKConverter.SUPPORTED_EXTENSIONS:
        all_files.extend(config.split_apk_dir.glob(f"*{ext}"))
    
    if not all_files:
        print(f"[X] split_apk目录下没有找到APKS/XAPK/APKM文件")
        print(f"    请将文件放入: {config.split_apk_dir}")
        return
    
    print(f"\n[*] 找到 {len(all_files)} 个文件:")
    for f in all_files:
        print(f"   - {f.name}")
    
    print("\n" + "="*60)
    print("开始批量转换 APKS/XAPK/APKM -> APK...")
    print("="*60)
    
    converter = SplitAPKtoAPKConverter(config)
    
    results = {
        "success": [],
        "failed": []
    }
    
    for i, file_path in enumerate(all_files, 1):
        print(f"\n[{i}/{len(all_files)}] 处理: {file_path.name}")
        
        try:
            result = converter.convert(file_path)
            if result:
                results["success"].append(file_path.name)
            else:
                results["failed"].append(file_path.name)
        except Exception as e:
            print(f"[X] 转换失败: {e}")
            import traceback
            traceback.print_exc()
            results["failed"].append(file_path.name)
    
    # 打印结果摘要
    print("\n" + "="*60)
    print("[*] 转换结果摘要")
    print("="*60)
    print(f"[OK] 成功: {len(results['success'])} 个")
    for name in results['success']:
        print(f"   - {name}")
    
    if results['failed']:
        print(f"[X] 失败: {len(results['failed'])} 个")
        for name in results['failed']:
            print(f"   - {name}")
    
    print(f"\n输出目录: {config.apk2_dir}")


def batch_convert_aab_to_apks(config, mode="default", all_modes=False):
    """批量转换AAB到APKS"""
    # 获取所有AAB文件
    aab_files = list(config.aab_dir.glob("*.aab"))
    
    if not aab_files:
        print("[X] aab目录下没有找到AAB文件")
        return
    
    print(f"\n[*] 找到 {len(aab_files)} 个AAB文件:")
    for aab in aab_files:
        print(f"   - {aab.name}")
    
    print("\n" + "="*60)
    if all_modes:
        print("开始批量转换（所有模式）...")
    else:
        print(f"开始批量转换（模式: {mode}）...")
    print("="*60)
    
    converter = AABtoAPKSConverter(config)
    
    results = {
        "success": [],
        "failed": []
    }
    
    for i, aab_file in enumerate(aab_files, 1):
        print(f"\n[{i}/{len(aab_files)}] 处理: {aab_file.name}")
        
        try:
            if all_modes:
                # 转换所有模式
                mode_results = converter.convert_all_modes(aab_file)
                if all(r == "success" for r in mode_results.values()):
                    results["success"].append(aab_file.name)
                else:
                    results["failed"].append(f"{aab_file.name} (部分模式失败)")
            else:
                # 单一模式转换
                result = converter.convert(aab_file, mode=mode)
                if result:
                    results["success"].append(aab_file.name)
                else:
                    results["failed"].append(aab_file.name)
        except Exception as e:
            print(f"[X] 转换失败: {e}")
            import traceback
            traceback.print_exc()
            results["failed"].append(aab_file.name)
    
    # 打印结果摘要
    print("\n" + "="*60)
    print("[*] 转换结果摘要")
    print("="*60)
    print(f"[OK] 成功: {len(results['success'])} 个")
    for name in results['success']:
        print(f"   - {name}")
    
    if results['failed']:
        print(f"[X] 失败: {len(results['failed'])} 个")
        for name in results['failed']:
            print(f"   - {name}")


def batch_convert_apk_to_aab(config):
    """批量转换APK到AAB"""
    # 获取所有APK文件
    apk_files = list(config.apk_dir.glob("*.apk"))
    
    if not apk_files:
        print("[X] apk目录下没有找到APK文件")
        return
    
    print(f"\n[*] 找到 {len(apk_files)} 个APK文件:")
    for apk in apk_files:
        print(f"   - {apk.name}")
    
    print("\n" + "="*60)
    print("开始批量转换...")
    print("="*60)
    
    converter = APKtoAABConverter(config)
    
    results = {
        "success": [],
        "failed": []
    }
    
    for i, apk_file in enumerate(apk_files, 1):
        print(f"\n[{i}/{len(apk_files)}] 处理: {apk_file.name}")
        
        try:
            result = converter.convert(apk_file, auto_sign=True)
            if result:
                results["success"].append(apk_file.name)
            else:
                results["failed"].append(apk_file.name)
        except Exception as e:
            print(f"[X] 转换失败: {e}")
            import traceback
            traceback.print_exc()
            results["failed"].append(apk_file.name)
    
    # 打印结果摘要
    print("\n" + "="*60)
    print("[*] 转换结果摘要")
    print("="*60)
    print(f"[OK] 成功: {len(results['success'])} 个")
    for name in results['success']:
        print(f"   - {name}")
    
    if results['failed']:
        print(f"[X] 失败: {len(results['failed'])} 个")
        for name in results['failed']:
            print(f"   - {name}")


def show_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("请选择操作:")
    print("="*60)
    print("  [1] APK -> AAB  (批量转换APK为AAB，自动生成随机签名)")
    print("  [2] AAB -> APKS (批量转换AAB为APKS)")
    print("  [3] APK -> AAB -> APKS (一键全流程转换)")
    print("-"*60)
    print("  AAB转APKS模式选项:")
    print("  [4] AAB -> APKS (default模式 - 拆分APK)")
    print("  [5] AAB -> APKS (universal模式 - 通用单APK)")
    print("  [6] AAB -> APKS (system模式 - 系统APK)")
    print("  [7] AAB -> APKS (instant模式 - 即时应用)")
    print("  [8] AAB -> APKS (所有模式)")
    print("-"*60)
    print("  拆分包转普通APK:")
    print("  [9] APKS/XAPK/APKM -> APK (转换拆分安装包为普通APK)")
    print("-"*60)
    print("  [0] 退出")
    print("="*60)


def show_mode_info():
    """显示bundletool模式说明"""
    print("\n" + "="*60)
    print("Bundletool 转换模式说明")
    print("="*60)
    modes_info = {
        "default": "默认模式\n   生成针对所有设备配置的拆分APK集合\n   包含: base APK + 配置APK (ABI/密度/语言)",
        "universal": "通用模式\n   生成单个包含所有资源和代码的APK\n   适用于: 测试、侧载安装",
        "system": "系统模式\n   生成用于预装到系统分区的APK\n   适用于: OEM厂商预装应用",
        "instant": "即时应用模式\n   生成即时应用APK (无需安装即可运行)\n   适用于: Google Play即时体验",
        "persistent": "持久模式\n   生成持久APK\n   适用于: 需要在系统中保持运行的应用",
        "archive": "存档模式\n   生成存档APK用于应用归档\n   适用于: 应用下架后保留访问入口"
    }
    for mode, desc in modes_info.items():
        print(f"\n[{mode}]")
        print(f"   {desc}")
    print("\n" + "="*60)


def main():
    """主函数"""
    # 获取脚本所在目录作为基础目录
    base_dir = Path(__file__).parent
    
    print("="*60)
    print("APK / AAB / APKS Converter Tool")
    print("APK/AAB/APKS 批量转换工具 v1.0")
    print("="*60)
    
    # 初始化配置
    config = Config(base_dir)
    
    # 验证工具
    print("\n[*] 检查工具...")
    if not config.validate():
        print("\n请确保所有必要的工具都已安装")
        sys.exit(1)
    
    # 检查并创建目录
    print("\n[*] 检查目录...")
    for dir_name, dir_path in [
        ("apk", config.apk_dir),
        ("aab", config.aab_dir),
        ("apks", config.apks_dir),
        ("split_apk", config.split_apk_dir),
        ("apk2", config.apk2_dir),
        ("keystore", config.keystore_dir)
    ]:
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"   创建目录: {dir_name}/")
        else:
            # 统计文件数量
            if dir_name == "apk":
                count = len(list(dir_path.glob("*.apk")))
            elif dir_name == "aab":
                count = len(list(dir_path.glob("*.aab")))
            elif dir_name == "apks":
                count = len(list(dir_path.glob("*.apks")))
            elif dir_name == "split_apk":
                count = sum(len(list(dir_path.glob(f"*{ext}"))) 
                           for ext in ['.apks', '.xapk', '.apkm'])
            elif dir_name == "apk2":
                count = len(list(dir_path.glob("*.apk")))
            elif dir_name == "keystore":
                count = len(list(dir_path.glob("*.jks")))
            else:
                count = 0
            print(f"   [OK] {dir_name}/ ({count} 个文件)")
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['1', 'apk2aab', 'apk-to-aab']:
            batch_convert_apk_to_aab(config)
        elif arg in ['2', 'aab2apks', 'aab-to-apks']:
            mode = sys.argv[2] if len(sys.argv) > 2 else "default"
            batch_convert_aab_to_apks(config, mode=mode)
        elif arg in ['3', 'all', 'full']:
            batch_convert_apk_to_aab(config)
            batch_convert_aab_to_apks(config, mode="default")
        elif arg in ['9', 'split2apk', 'split-to-apk', 'xapk2apk', 'apks2apk']:
            batch_convert_split_to_apk(config)
        elif arg in ['modes', 'help-modes']:
            show_mode_info()
        else:
            print(f"[!] 未知参数: {arg}")
            print("可用参数: 1, 2, 3, 9, apk2aab, aab2apks, all, split2apk, modes")
        return
    
    # 交互式菜单
    while True:
        show_menu()
        
        try:
            choice = input("\n请输入选项 [0-9]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n[*] 已退出")
            break
        
        if choice == '0':
            print("\n[*] 已退出")
            break
        elif choice == '1':
            batch_convert_apk_to_aab(config)
        elif choice == '2':
            batch_convert_aab_to_apks(config, mode="default")
        elif choice == '3':
            print("\n[*] 执行全流程转换: APK -> AAB -> APKS")
            batch_convert_apk_to_aab(config)
            batch_convert_aab_to_apks(config, mode="default")
        elif choice == '4':
            batch_convert_aab_to_apks(config, mode="default")
        elif choice == '5':
            batch_convert_aab_to_apks(config, mode="universal")
        elif choice == '6':
            batch_convert_aab_to_apks(config, mode="system")
        elif choice == '7':
            batch_convert_aab_to_apks(config, mode="instant")
        elif choice == '8':
            batch_convert_aab_to_apks(config, all_modes=True)
        elif choice == '9':
            batch_convert_split_to_apk(config)
        elif choice.lower() == 'h' or choice == '?':
            show_mode_info()
        else:
            print(f"\n[!] 无效选项: {choice}")
        
        input("\n按回车键继续...")


if __name__ == "__main__":
    main()
