# Q34) Compose Canvas

## Compose의 Canvas는 무엇인가요? {#what-is-compose-canvas}

`Canvas` 는 Compose에서 그리기 표면(drawing surface)에 직접 접근할 수 있게 해 주는 컴포저블로, 커스텀 그래픽이나 애니메이션, 시각 효과를 만들 때 사용됩니다. 일반 UI 컴포넌트와 달리, `DrawScope` 인터페이스를 통해 그리기 명령어를 직접 호출함으로써 렌더링을 정밀하게 제어할 수 있게 해 줍니다.

`Canvas` 는 Jetpack Compose의 그리기 시스템 위에서 동작하며, `drawRect`, `drawCircle`, `drawPath`, `drawText`, `drawImage` 같은 함수들을 사용할 수 있게 해 줍니다. 이 함수들로 커스텀 도형, 이미지, 벡터 그래픽을 효율적으로 그리고, 색상·크기·획 스타일·변환 등을 자유롭게 다룰 수 있습니다.

### 사용 예시 {#example-usage}

다음은 `Canvas` 컴포저블 안에 단순한 원을 그리는 예시입니다.

```kotlin
@Composable
fun DrawCircleCanvas() {
    Canvas(modifier = Modifier.size(200.dp)) {
        drawCircle(
            color = Color.Blue,
            radius = size.minDimension / 2,
            center = center
        )
    }
}
```
{title="CanvasExample.kt"}

이 예시에서:

- `Canvas` 컴포저블이 200.dp의 고정 크기를 가집니다.
- `drawCircle` 이 캔버스 중앙에 파란색 원을 그립니다.
- `size.minDimension / 2` 가 원이 캔버스 영역 안에 깔끔하게 들어가도록 만들어 줍니다.

### 기본 변환(Transformations) {#basic-transformations}

`Canvas` 컴포저블은 다양한 변환과 그리기 함수를 제공하므로, 동적이고 인터랙티브한 UI 요소를 만들기에 좋습니다. 핵심 연산은 다음과 같습니다.

- **Scaling (`scale`)**: 그리기 요소를 지정한 비율로 확대·축소합니다.
- **Translation (`translate`)**: X·Y 축을 따라 그리기 영역 안의 요소를 이동시킵니다.
- **Rotation (`rotate`)**: 회전축을 기준으로 요소를 회전시킵니다.
- **Inset (`inset`)**: 그리기 경계에 패딩을 적용합니다.
- **Multiple Transformations (`withTransform`)**: 여러 변환을 한 번에 결합해 성능을 개선합니다.
- **Text Drawing (`drawText`)**: 텍스트를 정밀한 위치·커스터마이즈와 함께 직접 렌더링합니다.

이러한 변환은 [컴포저블 수명 주기의 draw 단계](https://developer.android.com/develop/ui/compose/phases)에서만 적용된다는 점을 기억해야 합니다. 즉 변환은 요소의 레이아웃 크기나 위치 자체에는 영향을 주지 않으며, 변환을 통해 크기·위치를 바꾸더라도 실제 레이아웃 경계는 그대로 유지됩니다. 그 결과 변환된 요소가 자신의 레이아웃 영역 밖으로 삐져나가거나 다른 요소와 겹쳐 보일 수 있습니다.

### 요약 {#summary}

<tldr>

`Canvas` 는 커스텀 드로잉, 변환, 애니메이션을 만들기 위한 매우 유연한 도구입니다. 스케일링, 이동, 회전, 텍스트 렌더링 같은 변환을 지원해 정교한 커스텀 UI 디자인에 잘 어울립니다. `Canvas` 를 활용하면 앱에 특화된 시각적으로 풍부한 UI 컴포넌트를 직접 빚어낼 수 있습니다. 더 깊은 내용은 [Graphics in Compose](https://developer.android.com/develop/ui/compose/graphics/draw/overview#draw-image) 공식 문서를 참고할 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Canvas로 커스텀 애니메이션 원형 진행률(progress) 바를 만든다면 어떻게 구현하시겠습니까?">

가장 단순한 형태는 **`Canvas` + `drawArc` + `Animatable`** 의 조합입니다. 진행률을 0f~1f 범위의 `Animatable<Float>` 으로 두고, 이 값이 바뀔 때마다 `Canvas` 안에서 `drawArc` 의 `sweepAngle = progress * 360f` 를 그려 주면 자연스럽게 원이 차오르는 형태가 됩니다. 배경 트랙은 `drawArc(color = trackColor, startAngle = -90f, sweepAngle = 360f, useCenter = false, style = Stroke(width = trackWidth, cap = StrokeCap.Round))` 로 한 번 그리고, 그 위에 진행 호(arc)를 같은 시작 각도에서 진행률만큼만 그려 주면 두 호가 같은 위치에 정렬됩니다.

여기서 핵심은 **State 와의 결합** 입니다. `var progress by remember { Animatable(0f) }` 로 두고 `LaunchedEffect(targetProgress) { progress.animateTo(targetProgress, tween(durationMillis = 600, easing = FastOutSlowInEasing)) }` 형태로 외부 입력 변화에 반응해 애니메이션을 시작하면, 진행률 변화가 부드러운 보간으로 화면에 반영됩니다. 또한 `Canvas` 의 람다 안은 매 프레임 다시 그려지는 영역이므로, 색상이나 stroke 폭처럼 자주 바뀌지 않는 객체는 람다 바깥에서 `remember` 로 보관해 두는 편이 안전합니다.

마지막 마감은 **세부 디자인** 에서 결정됩니다. `useCenter = false` 와 `Stroke(cap = StrokeCap.Round)` 로 진행 호의 끝을 둥글게 만들고, 텍스트로 퍼센트를 함께 보여 주려면 `Box` 안에 `Canvas` 와 `Text` 를 겹쳐 두면 됩니다. 색상도 `Brush.sweepGradient` 나 `linearGradient` 로 바꾸면 같은 코드 구조에서 그라디언트 진행률 바를 곧바로 만들 수 있어, 디자인 시스템의 컴포넌트로 발전시키기 좋은 출발점이 됩니다.

</def>
</deflist>
