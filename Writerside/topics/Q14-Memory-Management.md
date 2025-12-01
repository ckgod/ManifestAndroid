# Q14) Memory Management

## Android는 메모리 관리를 어떻게 처리하며, 메모리 누수를 어떻게 방지하나요? {#Adff11}

Android는 사용되지 않는 메모리를 자동으로 회수하는 가비지 컬렉션 메커니즘을 통해 메모리를 관리하여, 활성 애플리케이션 및 서비스에 효율적인 할당을 보장합니다.
이는 관리되는 메모리 환경에 의존하므로, 개발자는 C++와 같은 언어에서처럼 메모리를 수동으로 할당하고 해제할 필요가 없습니다.
Dalvik 또는 ART 런타임(이 장에서 나중에 다룰 예정입니다)은 메모리 사용량을 모니터링하고, 더 이상 참조되지 않는 객체를 정리하며, 과도한 메모리 소비를 방지합니다.

Android는 시스템 메모리가 부족할 때 백그라운드 프로세스를 종료하기 위해 저메모리 킬러(low-memory killer)를 사용하여, 포그라운드 애플리케이션의 원활한 작동을 우선시합니다.
개발자는 시스템 성능에 미치는 영향을 최소화하기 위해 앱이 리소스를 효율적으로 활용하도록 해야 합니다.

### Android에서 메모리 누수 방지 방법

메모리 누수는 애플리케이션이 더 이상 필요 없는 객체에 대한 참조를 계속 유지하여, `garbage collector`가 메모리를 회수하는 것을 방지할 때 발생합니다.
일반적인 원인으로는 부적절한 생명주기 관리, 정적 참조, 또는 `Context`에 대한 장기적인 참조 유지가 있습니다.

#### 메모리 누수를 방지하기 위한 모범 사례

1.  **Lifecycle-Aware Component 사용**: `ViewModel` 및 `Flow`와 [`collectAsStateWithLifecycle`](https://developer.android.com/reference/kotlin/androidx/lifecycle/compose/package-summary#extension-functions) 또는 `LiveData`와 같은 `Lifecycle-Aware Component`를 활용하면 해당 `lifecycle`이 종료될 때 리소스가 올바르게 해제됩니다. 이러한 컴포넌트는 연결된 `lifecycle`이 더 이상 활성 상태가 아니거나 특정 상태로 전환될 때 자동으로 정리를 관리합니다.
2.  **Context에 대한 참조 유지 방지**: `static fields`나 `singletons`과 같은 수명이 긴 객체에서 `Activity` 또는 `Context`에 대한 참조를 유지하는 것을 피하세요. 대신, `activity`나 `fragment`의 `lifecycle`에 묶여 있지 않은 `ApplicationContext`를 가능한 한 사용하십시오.
3.  **리스너 및 콜백 등록 해제**: 항상 적절한 `lifecycle` 메서드에서 리스너, 옵저버 또는 콜백을 등록 해제하십시오. 예를 들어, `onPause()` 또는 `onStop()`에서 `BroadcastReceivers`를 등록 해제합니다.
4.  **중요하지 않은 객체에는 WeakReference 사용**: 강력한 참조가 필요 없는 객체에는 `WeakReference`를 사용하십시오. 이렇게 하면 메모리가 필요할 때 `garbage collector`가 해당 객체를 회수할 수 있습니다.
5.  **누수 감지 도구 사용**: [`LeakCanary`](https://square.github.io/leakcanary/)와 같은 도구를 활용하여 개발 중에 메모리 누수를 식별하고 수정하십시오. 이 도구는 어떤 객체가 메모리 누수를 일으키는지, 그리고 이를 해결하는 방법에 대한 통찰력을 제공합니다. 또한 `Android Studio`의 [`Memory Profiler`](https://developer.android.com/studio/profile/memory-profiler)를 활용하여 `stutter`, `freeze`, 심지어 앱 충돌로 이어질 수 있는 메모리 누수 및 메모리 `churn`을 식별할 수 있습니다.
6.  **View에 대한 Static 참조 방지**: `View`는 `Activity context`에 대한 참조를 유지하여 메모리 누수로 이어질 수 있으므로 `static fields`에 저장해서는 안 됩니다.
7.  **리소스 닫기**: 파일 스트림, `cursor`, 데이터베이스 연결과 같은 리소스는 더 이상 필요하지 않을 때 항상 명시적으로 해제하십시오. 예를 들어, 데이터베이스 쿼리 후 `Cursor`를 닫습니다.
8.  **Fragment 및 Activity 현명하게 사용**: `fragment`를 과도하게 사용하거나 `fragment` 간에 참조를 부적절하게 유지하는 것을 피하십시오. `onDestroyView()` 또는 `onDetach()`에서 `fragment` 참조를 정리하십시오.

### 요약
Android의 메모리 관리는 효율적이지만, 개발자가 메모리 누수를 방지하기 위한 모범 사례를 따르도록 요구합니다. 생명주기 인식(lifecycle-aware) 컴포넌트를 사용하고, `Context` 또는 뷰에 대한 정적 참조를 피하며, `LeakCanary`와 같은 도구를 활용하면 누수 발생 가능성을 크게 줄일 수 있습니다. 적절한 생명주기 이벤트 동안의 올바른 리소스 관리 및 정리 작업은 더 부드러운 앱 성능과 사용자 경험을 보장합니다.


<deflist collapsible="true" default-state="collapsed">
<def title="Q) 애플리케이션에서 메모리 누수의 일반적인 원인은 무엇이며, 개발자는 이를 어떻게 방지할 수 있습니까?">

</def>
<def title="Q) Android의 가비지 컬렉션(garbage collection) 메커니즘은 어떻게 작동하며, 개발자는 애플리케이션에서 메모리 누수를 감지하고 해결하기 위해 어떤 도구를 사용할 수 있습니까?">

</def>
</deflist>