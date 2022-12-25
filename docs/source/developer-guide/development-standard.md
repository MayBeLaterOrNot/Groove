## 开发规范

### 命名规范
* **包名**和**文件名**使用蛇形命名法
* **类**使用大驼峰命名法
* **函数**和**变量**使用小驼峰命名法，与 Qt 保持一致

### 项目结构
#### app
所有与图形界面相关的代码都放在此文件夹下，具体结构如下：
* **common** 文件夹：包含所有文件共享的函数和类
* **components** 文件夹：包含所有窗口共享的组件，比如按钮、菜单和对话框
* **View** 文件夹：包含各个界面，比如我的音乐界面、正在播放界面和主界面
* **resource** 文件夹：包含图标和样式表等资源文件
* **config** 文件夹：包含配置文件 `config.json`
* **cache** 文件夹：包含缓存的图片、数据库和日志

#### tests
用于存放测试用例，修改代码后应该允许再次运行测试用例来保证程序运行良好。

#### docs
用于存放项目文档，使用说明可以参见 [《Sphinx + Read the Docs 从懵逼到入门》](https://zhuanlan.zhihu.com/p/264647009)
