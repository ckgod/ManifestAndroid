# Q15) Side Effects

## 컴포저블 함수 내에서 Side Effects는 어떻게 처리하나요?

Jetpack Compose는 컴포저블의 리컴포지션 스코프 외부에서 작업을 처리할 수 있는 여러 [Side Effects Handler API](https://developer.android.com/develop/ui/compose/side-effects)를 제공합니다. 
이러한 API는 Android 프레임워크와의 상호 작용, 컴포지션 이벤트 관리, 상태 변화에 기반한 효과 트리거와 같은 시나리오를 처리하는 데 필수적입니다.

세 가지 주요 사이드 이펙트 핸들러 API인 `LaunchedEffect`, `DisposableEffect`, `SideEffect`에 대해 알아보겠습니다.

### 1. LaunchedEffect: 컴포저블 스코프 내에서 suspend functions 실행

LaunchedEffect는 컴포저블의 컴포지션 내에서 실행되는 `Coroutine`을 시작하는 데 사용됩니다. LaunchedEffect에 전달된 키가 변경되면 이 `Coroutine`은 취소되고 다시 시작됩니다. 이는 데이터 가져오기, 애니메이션 시작 또는 컴포저블이 컴포지션에 진입할 때 발생해야 하는 이벤트를 수신하는 등의 작업에 유용합니다.

주요 특징:
*   컴포저블이 컴포지션에 진입할 때 한 번 실행됩니다.
*   키가 변경되면 자동으로 취소되고 다시 시작됩니다.
*   컴포지션 인식: 컴포저블이 컴포지션을 떠날 때 자동으로 취소됩니다.
    예를 들어, 사용자가 목록의 항목을 클릭할 때 네트워크에서 추가 데이터를 가져와야 하는 경우, LaunchedEffect를 사용하여 이를 원활하게 처리할 수 있습니다. 이는 LaunchedEffect에 제공된 키 중 하나가 변경될 때마다 작업이 다시 실행될 수 있도록 보장합니다.

```kotlin
var selectedPoster: Poster by remember { mutableStateOf(null) }

LaunchedEffect(key1 = selectedPoster) {
    // ViewModel에 이벤트를 전송하여 네트워크에서 추가 정보 가져오기
}
```

또한 LaunchedEffect를 사용하여 `Flow`를 안전하게 관찰할 수 있습니다. LaunchedEffect에 의해 시작된 `Coroutine`은 컴포저블 함수가 컴포지션을 떠날 때 자동으로 취소되어 불필요한 리소스 사용을 방지합니다. 
또한, `Coroutine`은 리컴포지션 중에 다시 시작되지 않습니다. 
Effects가 호출 지점의 생명주기와 일치하도록 하려면 `Unit` 또는 `true`와 같은 상수를 키 매개변수로 전달할 수 있습니다. 
이는 키가 변경되지 않는 한 효과가 한 번만 실행되도록 보장합니다.

```kotlin
LaunchedEffect(key1 = Unit) {
    stateFlow
        .distinctUntilChanged()
        .filter { it.marked }
        .collect {  }
}
```

### 2. DisposableEffect: 정리가 필요한 effects

DisposableEffect는 컴포저블의 컴포지션에 바인딩된 리소스 또는 정리 작업을 관리하는 데 사용됩니다. 
LaunchedEffect와 달리, 컴포저블이 컴포지션을 떠날 때 리소스를 해제하기 위한 `onDispose` 람다가 포함된 `DisposableEffectScope`를 제공합니다.

주요 특징:
*   리스너, 옵저버 또는 구독과 같은 리소스 관리에 이상적입니다.
*   `onDispose` 콜백으로 적절한 정리를 보장합니다.
    예를 들어, 생명주기 이벤트에 기반하여 분석 이벤트를 전송해야 하는 경우, `LifecycleObserver`를 사용하여 이를 달성할 수 있습니다. DisposableEffect를 사용하여 컴포저블이 컴포지션에 진입할 때 옵저버를 등록하고, 컴포저블이 컴포지션을 떠날 때 자동으로 등록 해제할 수 있습니다. 이는 적절한 정리를 보장하고 메모리 누수를 방지합니다.

```kotlin
@Composable
fun HomeScreen(
    lifecycleOwner: LifecycleOwner = LocalLifecycleOwner.current,
    onStart: () -> Unit, // 'started' 분석 이벤트 전송
    onStop: () -> Unit // 'stopped' 분석 이벤트 전송
) {
    // 새로운 람다가 제공될 때 현재 람다를 안전하게 업데이트
    val currentOnStart by rememberUpdatedState(onStart)
    val currentOnStop by rememberUpdatedState(onStop)

    // lifecycleOwner가 변경되면 효과를 dispose하고 재설정
    DisposableEffect(lifecycleOwner) {
        // 분석 이벤트를 전송하기 위한 기억된 콜백을 트리거하는 옵저버 생성
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_START) {
                currentOnStart()
            } else if (event == Lifecycle.Event.ON_STOP) {
                currentOnStop()
            }
        }

        // 옵저버를 생명주기에 추가
        lifecycleOwner.lifecycle.addObserver(observer)

        // 효과가 Composition을 떠날 때, 옵저버 제거
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
        }
    }
}
```

### 3. SideEffect: Compose 상태를 비 Compose 코드에 발행

SideEffect는 모든 리컴포지션 직후 적용되어야 하는 작업을 실행하는 데 사용됩니다. 
이는 컴포저블이 리컴포지션된 후에 실행을 보장하므로, `ViewModel` 또는 외부 라이브러리에서 `UI` 상태를 업데이트하는 것과 같이 컴포지션의 일부가 아닌 외부 시스템과 Compose 상태를 동기화하는 데 적합합니다.

주요 특징:
*   모든 리컴포지션 후에 실행됩니다.
*   비 Compose 컴포넌트와의 상태 동기화에 유용합니다.

예를 들어, 분석 라이브러리가 사용자 집단을 커스텀 메타데이터(예: "user properties")를 후속 분석 이벤트에 첨부하여 분류하는 것을 지원하는 경우, SideEffect를 사용하여 현재 사용자의 사용자 유형이 원활하게 업데이트되도록 할 수 있습니다.
이 접근 방식은 라이브러리의 상태가 Compose 애플리케이션의 현재 상태와 동기화된 상태로 유지되도록 보장합니다.

```kotlin
@Composable
fun rememberFirebaseAnalytics(user: User): FirebaseAnalytics {
    val analytics: FirebaseAnalytics = remember {
        FirebaseAnalytics()
    }

    // 모든 성공적인 컴포지션에서 FirebaseAnalytics를 현재 User의 userType으로 업데이트하여,
    // 미래의 분석 이벤트에 이 메타데이터가 첨부되도록 보장
    SideEffect {
        analytics.setUserProperty("userType", user.userType)
    }
    return analytics
}
```

SideEffect 사용의 또 다른 예는 아래 예시와 같이 리컴포지션이 완료된 후에만 Lottie 애니메이션을 시작하거나 비 컴포저블 액션을 트리거해야 할 때입니다.

```kotlin
SideEffect {
    lottieAnimationView.playAnimation() // 최신 리컴포지션 후에만
}
```

### Summary
각 사이드 이펙트 핸들러 API는 고유한 목적을 가집니다.

*   LaunchedEffect는 `Coroutine` 기반 작업을 시작하거나 키 매개변수 변경에 따라 작업을 다시 시작하는 데 사용합니다.
*   DisposableEffect는 컴포저블의 컴포지션에 연결된 리소스를 관리하고 정리하는 데 사용합니다.
*   SideEffect는 모든 리컴포지션 직후 적용되어야 하는 작업을 실행하고 외부 시스템을 Compose 상태와 동기화하는 데 사용합니다.

이러한 사이드 이펙트 핸들러 API를 언제 어떻게 사용해야 하는지 이해하면 깔끔하고 선언적인 접근 방식을 유지하면서 Side Effects를 효과적으로 관리하는 데 도움이 될 수 있습니다. 세 가지 주요 사이드 이펙트 핸들링 API의 내부 동작과 작동 방식에 대한 더 깊은 이해를 위해서는 [Understanding the Internals of Side-Effect Handlers in Jetpack Compose](https://medium.com/proandroiddev/understanding-the-internals-of-Side-Effect-handlers-in-Jetpack-Compose-d55fbf914fde)를 확인하십시오.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) LaunchedEffect는 컴포저블에서 suspend functions를 관리하는 데 어떻게 도움이 되며, 키가 변경되면 어떤 일이 발생하나요?">

LaunchedEffect는 컴포저블의 생명주기에 연결된 코루틴 스코프를 제공하여, suspend 함수를 안전하게 실행할 수 있게 해줍니다.
key가 변경되면, LaunchedEffect는 기존의 실행 중이던 코루틴을 즉시 취소하고, 새로운 key 값으로 새 코루틴을 시작합니다.

</def>
<def title="Q) LaunchedEffect 대신 DisposableEffect를 언제 사용하시겠습니까?">

DisposableEffect는 명시적인 `onDispose` 정리 블록이 필요할 때 사용합니다.
LaunchedEffect도 코루틴을 취소하는 정리 작업을 하지만, DisposableEffect는 코루틴이 아닌 리스너, 옵저버, 콜백 등을 등록하고, Composable이 사라질 때 이를 수동으로 해제해야 하는 경우에 특화되어 있습니다.

예를 들어 LifecyclerObserver 등록 및 해제가 있습니다. onResume, onPause같은 화면 생명주기 이벤트를 받아야할 때, 옵저버를 등록해주고 명시적으로 해제할 수 있습니다.

</def>
<def title="Q) SideEffect의 사용 사례와 LaunchedEffect와의 차이점을 설명해 주세요.">

SideEffect는 매 **리컴포지션**이 성공적으로 완료될 때마다 suspend 함수가 아닌 일반 코드를 실행해야 할 때 사용합니다.
LaunchedEffect와의 가장 큰 차이점은 실행 시점과 코루틴 스코프의 유무입니다.

간단히 말해, SideEffect는 Compose의 State를 Compose가 아닌 외부 세계와 동기화하기 위한 매우 드물게 사용되는 Effect 입니다.

가장 대표적인 예: 외부 애널리틱스 라이브러리와 연동

Composable 본문에 직접 작성하면 리컴포지션이 취소되어도, 실행될 수 있어 로그가 부정확하게 쌓이게 됩니다.

</def>
</deflist> 