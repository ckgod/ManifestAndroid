# Details: 여러 Activity 간 수명 주기 변화

Activity lifecycle에 대한 일반적인 후속 질문은 다음과 같을 수 있습니다.
"Activity A를 시작한 다음 Activity B를 시작하고, 마지막으로 Activity A로 순차적으로 돌아갈 때 발생하는 lifecycle 전환을 설명할 수 있습니까?" 
이 시나리오는 Android 시스템이 여러 Activity 상태를 관리하는 방식에 대한 이해도를 테스트하는 데 도움이 됩니다.

Activity A와 Activity B 두 Activity 사이를 탐색할 때, 각 Activity에 대한 Android lifecycle 콜백은 특정 순서로 호출됩니다.
이 시나리오에 대한 lifecycle 전환을 단계별로 살펴보겠습니다.

## Activity A 및 Activity B의 완전한 순차적 Lifecycle 흐름

*   **Activity A의 초기 실행**:
    *   **Activity A**: 처음 실행될 때 `onCreate()` -> `onStart()` -> `onResume()` 순서로 진행됩니다. 사용자는 Activity A와 상호작용합니다.

*   **Activity A에서 Activity B로 이동**:
    *   **Activity A**: `onPause()`가 호출되어 UI를 일시 중지하고 보이는 상태와 연결된 리소스를 해제합니다.
    *   **Activity B**: `onCreate()` -> `onStart()` -> `onResume()`이 호출되어 포커스를 얻고 포그라운드 Activity가 됩니다.
    *   **Activity A**: `onStop()`이 호출됩니다 (액티비티 B가 액티비티 A를 완전히 가리는 경우에만 해당).

*   **Activity B에서 Activity A로 돌아가기**:
    *   **Activity B**: `onPause()`
    *   **Activity A**: `onRestart()` -> `onStart()` -> `onResume()`이 호출되어 포커스를 되찾고 포그라운드로 돌아옵니다.
    *   **Activity B**: `onStop()` -> `onDestroy()`

## 요약

두 Activity 간에 전환할 때, 포그라운드 Activity는 백그라운드로 이동하기 전에 항상 `onPause()` lifecycle을 거칩니다.
새로 시작되는 Activity는 `onCreate()`부터 시작되는 lifecycle과 함께 포커스를 가져옵니다.
이전 Activity로 돌아갈 때, `onRestart()` 또는 `onResume()`을 사용하여 일시 중지된 상태에서 다시 시작되며, 나가는 Activity는 동작에 따라 `stop`되거나 `destroy`됩니다.
이러한 lifecycle 전환을 이해하는 것은 적절한 리소스 관리와 원활한 사용자 경험을 보장합니다.