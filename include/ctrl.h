#ifndef CTRL_H
#define CTRL_H

#include "stdio.h"
#include <stdint.h>
#include <Arduino.h>
#include "pid.h"
typedef struct 
{
   	float position;	 // m
	float speedCmd;	 // m/s
	float speed;    // m/s
	float yawSpeedCmd; // rad/s
	float yawAngle;	 // rad
	float rollAngle; // rad
	float legLength; // m
	float target; // m
	bool crossStepEnabled; // 交叉步使能标志
}Target;


typedef struct 
{
	float theta, dTheta;
	float x, dx;
	float phi, dPhi;
} StateVar;

//站立过程状态枚举量
typedef enum  {
	StandupState_None,
	StandupState_Prepare,
	StandupState_Standup,
} StandupState;

typedef struct GroundDetector
{
    float leftSupportForce, rightSupportForce;
    bool isTouchingGround, isCuchioning;
} GroundDetector;


extern Target target;
extern StateVar stateVar;
extern StandupState standupState;
extern bool balanceEnabled; // 平衡站立使能标志
extern bool legTestMode; // 腿部测试模式标志（右扳机按住时生效）

void Ctrl_Init(void);
void StandUp(void);
void Ctrl_LoopLogStart(uint32_t sampleTarget);
void Ctrl_LoopLogStop(void);
void Ctrl_LoopLogDump(void);
void Ctrl_LoopLogDumpTo(Print &out);
uint32_t Ctrl_LoopLogDumpRangeTo(Print &out, uint32_t start, uint32_t maxCount);
void Ctrl_LoopLogStatsTo(Print &out, uint16_t binWidthUs);

#endif
