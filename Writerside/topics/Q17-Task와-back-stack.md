# Q17) Task와 back stack

## Task와 back stack이란 무엇인가요?

[Task](https://developer.android.com/guide/components/activities/tasks-and-back-stack)는 사용자가 특정 목표를 달성하기 위해 상호작용하는 Activity들의 모음입니다.
Task는 back stack으로 구성되는데, 이는 Activity가 시작될 때 추가되고 사용자가 뒤로 이동하거나 시스템이 리소스를 회수할 때 제거되는 last-in, first-out (LIFO) 구조입니다.

### Tasks

Task는 Activity가 시작될 때, 일반적으로 런처나 Intent를 통해 시작됩니다.
Intent 및 Activity launch mode가 어떻게 구성되었는지에 따라, Task는 여러 애플리케이션과 그들의 Activity에 걸쳐 있을 수 있습니다.
예를 들어, 이메일 앱에서 링크를 클릭하면 동일한 Task의 일부로 브라우저가 열릴 수 있습니다.
Task는 관련 Activity가 파괴될 때까지 활성 상태를 유지합니다.

### Back Stack

back stack은 Task 내의 Activity 기록을 유지합니다.
사용자가 새 Activity로 이동하면 현재 Activity가 스택에 푸시됩니다.
뒤로 가기 버튼을 누르면 스택의 최상단 Activity가 팝(pop)되고, 그 아래에 있는 Activity가 재개됩니다. 이 메커니즘은 사용자 워크플로우에서 직관적인 탐색과 연속성을 보장합니다.

Task와 back stack은 Activity launch mode와 intent flag의 영향을 받습니다.
launch mode와 intent flag는 Task와 back stack 내에서 Activity의 동작을 제어하는 데 사용되는 메커니즘입니다.
이러한 구성은 개발자가 Activity가 어떻게 시작되고 다른 Activity와 어떻게 상호작용하는지 정의할 수 있게 합니다.

### Launch Modes

Launch mode는 Activity가 인스턴스화되고 back stack에서 처리되는 방식을 결정합니다.

Android에는 네 가지 주요 launch mode가 있습니다:

1. **`standard`**: 기본 launch mode입니다. Activity가 시작될 때마다, 인스턴스가 이미 존재하더라도 새로운 인스턴스가 생성되어 back stack에 추가됩니다.

2. **`singleTop`**: Activity 인스턴스가 back stack의 최상단에 이미 존재한다면, 새로운 인스턴스는 생성되지 않습니다. 대신, 기존 인스턴스가 `onNewIntent()`에서 Intent를 처리합니다.

3. **`singleTask`**: Task 내에 Activity의 인스턴스는 하나만 존재합니다. 인스턴스가 이미 존재한다면, 해당 인스턴스가 전면으로 가져와지고 `onNewIntent()`가 호출됩니다. 이는 앱의 진입점 역할을 하는 Activity에 유용합니다.

4. **`singleInstance`**: `singleTask`와 유사하지만, Activity는 다른 Activity와 분리된 자체 Task에 배치됩니다. 이는 다른 Activity가 동일한 Task의 일부가 될 수 없도록 보장합니다.

### Intent Flags

Intent flag는 Intent가 전송될 때 Activity가 시작되는 방식이나 back stack이 동작하는 방식을 수정하는 데 사용됩니다.

일반적으로 사용되는 몇 가지 플래그는 다음과 같습니다:

- **`FLAG_ACTIVITY_NEW_TASK`**: 새 Task에서 Activity를 시작하거나, Task가 이미 존재한다면 전면으로 가져옵니다.

- **`FLAG_ACTIVITY_CLEAR_TOP`**: Activity가 back stack에 이미 존재한다면, 그 위에 있는 모든 Activity가 지워지고 기존 인스턴스가 Intent를 처리합니다.

- **`FLAG_ACTIVITY_SINGLE_TOP`**: Activity가 back stack의 최상단에 있다면, 새로운 인스턴스가 생성되지 않도록 보장합니다. 이는 일반적으로 다른 플래그와 함께 사용됩니다.

- **`FLAG_ACTIVITY_NO_HISTORY`**: Activity가 back stack에 추가되는 것을 방지합니다. 즉, 종료된 후에도 지속되지 않습니다.

### Use Cases

- **Launch Mode**: 주로 AndroidManifest.xml 파일의 `<activity>` 태그 아래에 선언되어, 개발자가 Activity에 대한 기본 동작을 설정할 수 있게 합니다.

- **Intent Flag**: Intent를 생성할 때 프로그래밍 방식으로 적용되어, 특정 시나리오에 더 많은 유연성을 제공합니다.

## 예시

```kotlin
val intent = Intent(this, SecondActivity::class.java).apply {
    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
}
startActivity(intent)
```

이 예시에서, SecondActivity가 현재 Task에 이미 존재한다면, 그 위에 있는 모든 Activity가 지워지고 기존 인스턴스가 새 Intent를 받게 됩니다.
존재하지 않는다면, 새 인스턴스가 생성되어 현재 Task에 추가됩니다.

## 요약

Task와 back stack은 Android의 내비게이션 모델의 핵심이며, Activity의 생명주기와 내비게이션 히스토리를 관리함으로써 사용자 친화적인 워크플로우를 가능하게 합니다.

Launch mode는 Activity가 Task 내에서 시작되고 관리되는 방법에 대한 기본 동작을 정의하며, intent flag는 유사한 동작에 대한 런타임 제어를 제공합니다.
이들을 함께 사용하여 Activity 생명주기와 back stack 내비게이션을 정확하게 관리할 수 있습니다.

더 자세한 정보는 [Tasks and the back stack](https://developer.android.com/guide/components/activities/tasks-and-back-stack)을 확인하십시오.

## 면접 질문

**Q1.** `singleTask`와 `singleInstance` launch mode의 차이점은 무엇이며, 각각 어떤 시나리오에서 사용하시겠습니까?

**Q2.** 다양한 Activity launch mode에는 어떤 것들이 있으며, 이들은 Task와 back stack 동작에 어떻게 영향을 미칩니까?

