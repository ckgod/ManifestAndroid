# Q13) remember, rememberSaveable

## remember와 rememberSaveable의 차이점은 무엇인가요?
`Jetpack Compose`에서 상태 관리는 `UI`가 데이터 변경에 동적으로 반응하도록 하는 핵심 개념입니다. 
`remember`와 `rememberSaveable`은 모두 리컴포지션 간에 상태를 유지하는 `API`이지만, 서로 다른 목적을 가지고 있으며 특정 시나리오에 적합합니다.

### remember 이해하기
* **목적**: `remember` `API`는 값을 메모리에 저장하고 리컴포지션 간에 유지합니다. 그러나 화면 회전이나 프로세스 재시작과 같은 구성 변경 중에는 상태를 유지하지 않습니다.
* **사용 사례**: 상태가 구성 변경을 통해 유지될 필요가 없을 때 `remember`를 사용합니다. 예를 들어, 회전 시 재설정되는 임시 카운터 등이 있습니다.

```kotlin
@Composable
fun RememberExample() {
    var count by remember { mutableStateOf(0) }

    Button(onClick = { count++ }) {
        Text("Clicked $count times")
    }
}
```

* **동작**: `remember`는 현재 컴포지션 수명 주기 내에서만 상태를 저장하므로, 기기가 회전하면 `count` 변수가 0으로 재설정됩니다.

### rememberSaveable 이해하기
* **목적**: `rememberSaveable` `API`는 구성 변경 전반에 걸쳐 상태를 유지하여 `remember`를 확장합니다. `Bundle`에 저장될 수 있는 값을 자동으로 저장하고 복원합니다.
* **사용 사례**: 폼 입력이나 내비게이션 상태와 같이 구성 변경 시에도 유지되어야 하는 상태에 `rememberSaveable`을 사용합니다.

```kotlin
@Composable
fun RememberSaveableExample() {
    var text by rememberSaveable { mutableStateOf("") }

    OutlinedTextField(
        value = text,
        onValueChange = { text = it },
        label = { Text("Enter text") }
    )
}
```

* **동작**: `text` 값은 화면 회전이나 구성 변경에도 유지되어 원활한 사용자 경험을 보장합니다.

> 리컴포지션을 돕는 동시에 구성 변경에도 상태를 보존하여 궁극적으로 더 부드러운 사용자 경험을 제공한다면, 항상 `rememberSaveable`을 사용하는 것이 더 좋지 않을까요? 훌륭한 질문입니다!
> 
> 이에 대해서는 잠시 후 더 자세히 알아보겠지만, 지금으로서는 `remember`와 `rememberSaveable`이 이름상으로는 비슷해 보일 수 있지만, 내부 구현은 상당히 다르다는 점을 알아두는 것이 중요합니다.
> `rememberSaveable`은 `remember`에 비해 훨씬 더 많은 내부 처리를 수행하며 더 많은 오버헤드를 동반합니다.
> 이 때문에 모든 상황에서 무분별하게 `rememberSaveable`을 사용하면 앱 성능을 저하시키고 사용자 경험에 부정적인 영향을 미칠 수 있습니다. 
> 개발에는 만능 해결책이 거의 없습니다. 항상 장단점이 있으며, 모든 상황에 완벽한 도구는 없습니다.

### Key Differences (주요 차이점)

| 특성              | remember                 | rememberSaveable            |
|:----------------|:-------------------------|:----------------------------|
| 지속성             | 현재 컴포지션 수명 주기 동안만 상태 유지. | 컴포지션 및 구성 변경 시에도 상태 유지.     |
| 저장 위치           | 메모리에 값 저장.               | 메모리에 값을 저장하고 `Bundle`에도 저장. |
| Custom Saver 지원 | 해당 없음.                   | 복잡한 객체를 위한 Custom Saver 지원. |

### 언제 사용해야 하는가
* `remember`는 애니메이션이나 임시 `UI` 상태와 같이 현재 컴포지션 이후에는 지속될 필요가 없는 일시적인 상태에 사용합니다.
* `rememberSaveable`은 사용자 입력, 선택 상태 또는 폼 데이터와 같이 구성 변경 전반에 걸쳐 유지되어야 하는 상태에 사용합니다.

## 요약
`remember`와 `rememberSaveable`은 `Jetpack Compose`에서 상태를 관리하는 데 필수적인 `API`입니다. 

`remember`는 단일 컴포지션 내의 일시적인 상태에 적합하지만, `rememberSaveable`은 구성 변경 전반에 걸쳐 상태 지속성을 보장합니다.
하지만 `rememberSaveable`의 추가 기능에는 약간의 오버헤드가 따르므로 모든 시나리오에서 항상 최선의 선택은 아닙니다.
이들의 차이점을 이해하고 각 `API`를 적절하게 사용하면 애플리케이션의 필요에 따라 가장 효율적인 `API`를 선택하는 데 도움이 됩니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) `remember`보다 `rememberSaveable`을 사용하는 것이 선호되는 상황은 언제이며, 어떤 장단점을 고려해야 할까요?">

remember는 컴포저블이 화면에 있는 동안에만 상태를 기억하지만, rememberSaveable은 화면 회전이나 앱이 백그라운드로 갔다 오는 상황에서도 상태를 기억합니다.

애니메이션이나 단순한 UI 상태와 같이 컴포지션 이후에 지속될 필요가 없는 일시적인 상태에는 remember를 사용하고, 사용자 입력이나 중요한 UI 상태가 예기치 않게 사라지는 것을 막고 싶을 때는 rememberSaveable을 사용합니다.

rememberSaveable은 상태를 Bundle에 저장하고 복원하는 비용에 있어서 remember보다 비용이 높으며, 저장 타입에 제한이 있습니다. 따라서 Int, String, Boolean 같은 primitive 타입이나 Parcelable 인터페이스를 구현한 객체만 자동으로 저장할 수 있습니다.

</def>
<def title="Q) `rememberSaveable`에서 기본적으로 지원되지 않는 custom non-primitive state를 저장하는 방법은 무엇인가요?">

크게 두 가지가 있습니다.

1. 클래스를 Parcelable로 만들기

클래스 자체를 Parcelable로 만들면, rememberSaveable이 추가 설정 없이 자동으로 저장하고 복원할 수 있습니다.
Kotlin에서는 `@Parcelize`어노테이션으로 이 작업을 매우 쉽게 처리할 수 있습니다.

2. 커스텀 Saver 객체 제공하기

`@Parcelize` 어노테이션을 사용할 수 없는 경우(예: 외부 라이브러리 클래스, Parcelable로 만들 수 없는 멤버가 있는 경우) Saver를 직접 구현해야 합니다.

Saver는 rememberSaveable에게 이 객체를 어떻게 분해해서 저장하고, 어떻게 다시 조립해서 복원할지 알려주는 번역기입니다.

</def>
</deflist>