# Details: 애니메이션 Interpolator

## Interpolator는 애니메이션에서 어떻게 동작하나요? {#how-interpolator-works}

`Interpolator`는 시간에 따른 애니메이션 값의 변화율을 수정하여 애니메이션이 어떻게 진행될지를 정의합니다. 가속, 감속, 또는 일정한 속도 등을 제어하여 애니메이션을 더 자연스럽거나 시각적으로 매력적으로 만들어 줍니다.

Interpolator는 애니메이션의 시작값과 끝값 사이에서 진행 방식을 결정합니다. 예를 들어, 천천히 시작하여 빠르게 가속했다가 멈추기 전에 다시 느려지는 효과를 만들 수 있습니다. 이를 통해 단순한 선형 진행을 넘어 훨씬 풍부한 애니메이션 표현이 가능합니다.

### Android 기본 제공 Interpolator {#built-in-interpolators}

Android는 자주 사용되는 효과를 위한 여러 Interpolator를 기본으로 제공합니다.

| Interpolator | 동작 설명 |
|---|---|
| `LinearInterpolator` | 일정한 속도로 진행, 가속/감속 없음 |
| `AccelerateInterpolator` | 느리게 시작하여 점점 빨라짐 |
| `DecelerateInterpolator` | 빠르게 시작하여 끝으로 갈수록 느려짐 |
| `AccelerateDecelerateInterpolator` | 가속 후 감속하는 부드러운 효과 |
| `BounceInterpolator` | 물체가 튀는 것처럼 바운스 효과 |
| `OvershootInterpolator` | 목표값을 초과한 후 다시 돌아와 정착 |

`ObjectAnimator`, `ValueAnimator`, `ViewPropertyAnimator` 등 모든 애니메이션 객체에 `setInterpolator()` 메서드로 Interpolator를 적용할 수 있습니다.

```kotlin
val animator = ObjectAnimator.ofFloat(view, "translationY", 0f, 500f)
animator.duration = 1000
animator.interpolator = OvershootInterpolator()
animator.start()
```
{title="InterpolatorExample.kt"}

이 예시에서 `OvershootInterpolator`는 뷰가 목표 위치를 살짝 지나쳤다가 최종 위치로 돌아오게 하여 동적이고 생동감 있는 효과를 만들어 냅니다.

### 커스텀 Interpolator 구현 {#custom-interpolator}

`Interpolator` 인터페이스를 구현하고 `getInterpolation()` 메서드를 오버라이드하면 완전히 커스텀한 애니메이션 타이밍을 만들 수 있습니다.

```kotlin
class CustomInterpolator : Interpolator {
    override fun getInterpolation(input: Float): Float {
        // 2차 함수로 진행: 느리게 시작해서 빠르게 가속
        return input * input
    }
}

// 커스텀 Interpolator 적용
animator.interpolator = CustomInterpolator()
```
{title="CustomInterpolator.kt"}

`getInterpolation(input: Float)` 메서드의 `input`은 0.0(시작)부터 1.0(끝)까지의 값을 받으며, 반환값이 실제 애니메이션 진행률로 사용됩니다. 위 예시는 2차 함수(`input * input`)를 적용하여 처음에는 느리고 갈수록 빠르게 진행하는 가속 효과를 만듭니다.

### 요약 {#summary}

Interpolator는 Android 애니메이션의 타이밍과 진행 방식을 제어하여, 더 시각적으로 매력적이고 현실감 있는 효과를 만드는 핵심 도구입니다. [Android에서 제공하는 기본 Interpolator](https://medium.com/mindorks/understanding-interpolators-in-android-ce4e8d1d71cd)를 활용하면 대부분의 공통 케이스를 쉽게 처리할 수 있으며, `Interpolator` 인터페이스를 직접 구현하면 고유한 애니메이션 동작을 자유롭게 정의할 수 있습니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) OvershootInterpolator와 BounceInterpolator의 차이점은 무엇이며, 각각 언제 사용하나요?">

두 Interpolator 모두 목표값을 초과하는 동작을 포함하지만 동작 방식이 다릅니다.

- **OvershootInterpolator**: 애니메이션이 목표값을 살짝 초과한 후 다시 되돌아와 최종값에 정착합니다. UI 요소가 "딱" 하고 제자리에 들어오는 느낌을 줄 때 적합합니다. 예: 버튼 팝업, 카드 등장 등.

- **BounceInterpolator**: 목표값에 도달한 후 위아래로 여러 번 튀기는 효과를 냅니다. 물체가 바닥에 떨어지는 것처럼 물리적인 탄성을 표현할 때 적합합니다. 예: 공이 바닥에 닿는 애니메이션, 알림 아이콘 등장 등.

두 효과 모두 사용자의 시선을 끌어야 할 때 효과적이지만, 과도하게 사용하면 UI가 산만해질 수 있으므로 중요한 요소에만 선택적으로 적용하는 것이 좋습니다.

</def>
</deflist>
