#ifndef SERIAL_H
#define SERIAL_H

void Serial_Init(void);

// 查询串口指令队列是否忙（运行或暂停），用于在BLE输入侧做仲裁
bool Serial_IsQueueBusy(void);

// 处理一整行命令。UART2 和其他输入通道都应走这里，保证特殊命令行为一致。
int Serial_HandleCommandLine(const char *line);

// 兼容旧计划中的命名：注入一行命令并按需启动队列。
int Serial_InjectCommandLine(const char *line);
void Serial_TryStartQueue(void);

#endif
