# Q36) Compose 비주얼 애니메이션

## Jetpack Compose에서 비주얼 애니메이션을 어떻게 구현하나요? {#how-to-implement-animations}

Jetpack Compose는 UI 상태 사이의 부드러운 전환을 표현할 수 있는 선언형 애니메이션 시스템을 제공합니다. 내장 API들로 컴포저블의 표시 여부, 콘텐츠 변화, 크기 조정, 프로퍼티 전환 등을 손쉽게 애니메이션화할 수 있어, 사용자 경험을 끌어올리면서도 성능을 유지할 수 있습니다.

### AnimatedVisibility로 등장·사라짐 다루기 {#animated-visibility}

`AnimatedVisibility` 는 컴포저블의 진입/이탈 트랜지션에 애니메이션을 적용할 수 있게 해 줍니다. 기본적으로 등장 시에는 페이드 인 + 확장 효과를, 사라질 때는 페이드 아웃 + 축소 효과를 적용합니다. `EnterTransition` 과 `ExitTransition` 으로 커스텀 트랜지션을 정의할 수도 있습니다.

```kotlin
@Composable
fun AnimatedVisibilityExample() {
    var isVisible by remember { mutableStateOf(true) }

    Column {
        Button(onClick = { isVisible = !isVisible }) {
            Text("Toggle Visibility")
        }

        AnimatedVisibility(
            visible = isVisible,
            enter = fadeIn() + expandVertically(),
            exit = fadeOut() + shrinkVertically()
        ) {
            Box(
                modifier = Modifier
                    .size(100.dp)
                    .background(Color.Blue)
            )
        }
    }
}
```
{title="AnimatedVisibilityExample.kt"}

`Box` 가 등장할 때는 페이드 인 + 확장으로, 사라질 때는 페이드 아웃 + 축소로 자연스럽게 전환됩니다. `EnterTransition`/`ExitTransition` 으로 효과를 자유롭게 조합할 수 있습니다.

### Crossfade로 상태 사이의 부드러운 전환 {#crossfade}

`Crossfade` 는 두 컴포저블 사이의 전환을 페이드 효과로 다뤄 줍니다. 컴포넌트 전환이나 상태 변화에 자연스럽게 어울리는 도구입니다.

```kotlin
@Composable
fun CrossfadeExample() {
    var selectedScreen by remember { mutableStateOf("Home") }

    Column {
        Row {
            Button(onClick = { selectedScreen = "Home" }) { Text("Home") }
            Button(onClick = { selectedScreen = "Profile" }) { Text("Profile") }
        }

        Crossfade(targetState = selectedScreen) { screen ->
            when (screen) {
                "Home" -> Text("Home Screen", fontSize = 24.sp)
                "Profile" -> Text("Profile Screen", fontSize = 24.sp)
                else -> Text("Undefined Screen", fontSize = 24.sp)
            }
        }
    }
}
```
{title="CrossfadeExample.kt"}

Home 과 Profile 사이를 오갈 때 콘텐츠가 부드럽게 페이드 전환됩니다. 탭 내비게이션, 화면/이미지/컴포넌트 전환에 잘 어울립니다.

### AnimatedContent로 콘텐츠 변화 다루기 {#animated-content}

`AnimatedContent` 는 레이아웃은 유지한 채 콘텐츠 상태가 바뀔 때 매끄럽게 전환해 줍니다.

```kotlin
@Composable
fun AnimatedContentExample() {
    var count by remember { mutableStateOf(0) }

    Column {
        Button(onClick = { count++ }) { Text("Increment") }

        AnimatedContent(targetState = count) { targetCount ->
            Text(text = "Count: $targetCount", fontSize = 24.sp)
        }
    }
}
```
{title="AnimatedContentExample.kt"}

`count` 가 바뀔 때마다 `Text` 가 부드럽게 전환되며, 다른 애니메이션 스펙으로 커스터마이즈할 수도 있습니다.

### animate*AsState로 프로퍼티 애니메이션 다루기 {#animate-as-state}

`animate*AsState` 함수들은 단일 값을 부드럽게 보간해 주는 가장 직관적인 애니메이션 API입니다. 목표 값(target value)만 지정하면 현재 상태에서 목표 상태까지의 전환을 자동으로 처리해 줍니다. `animateDpAsState`, `animateFloatAsState`, `animateIntAsState`, `animateOffsetAsState`, `animateSizeAsState`, `animateValueAsState` 처럼 다양한 타입을 지원해 자연스러운 표현이 가능합니다.

다음 예시는 `animateDpAsState` 로 컴포넌트 크기를 동적으로 조정하는 모습입니다.

```kotlin
@Composable
fun AnimateAsStateExample() {
    var isExpanded by remember { mutableStateOf(false) }

    val boxSize by animateDpAsState(
        targetValue = if (isExpanded) 200.dp else 100.dp,
        animationSpec = tween(durationMillis = 500)
    )

    Column {
        Button(onClick = { isExpanded = !isExpanded }) {
            Text("Toggle Size")
        }

        Box(
            modifier = Modifier
                .size(boxSize)
                .background(Color.Green)
        )
    }
}
```
{title="AnimateAsStateExample.kt"}

`animateDpAsState` 가 500ms 동안 Dp 값을 보간하며, 토글 시점에 부드러운 크기 전환이 만들어집니다.

### animateContentSize로 크기 변화 다루기 {#animate-content-size}

`animateContentSize` 는 레이아웃의 크기 변화를 자동으로 애니메이션화해 줍니다. 별도의 콜백 없이 크기 변화를 매끄럽게 다룰 수 있습니다.

```kotlin
@Composable
fun AnimateContentSizeExample() {
    var expanded by remember { mutableStateOf(false) }

    Column {
        Button(onClick = { expanded = !expanded }) {
            Text("Expand/Collapse")
        }

        Box(
            modifier = Modifier
                .background(Color.Red)
                .animateContentSize()
                .padding(16.dp)
        ) {
            Text(
                text = if (expanded) "Expanded Text with more content" else "Short Text",
                fontSize = 18.sp
            )
        }
    }
}
```
{title="AnimateContentSizeExample.kt"}

`Box` 가 콘텐츠 변화에 따라 부드럽게 리사이즈되며, 별도의 애니메이션 로직이 필요하지 않습니다.

### 요약 {#summary}

<tldr>

Jetpack Compose는 XML 기반 애니메이션에 비해 훨씬 단순한 형태로 사용할 수 있는 다양한 애니메이션 API를 제공합니다. **AnimatedVisibility** 로 등장·사라짐을, **Crossfade** 로 UI 상태 전환을, **AnimatedContent** 로 콘텐츠 갱신을 다룰 수 있고, **animate*AsState** 로 크기·투명도·위치 같은 단일 값을 보간하며, **animateContentSize** 로 추가 로직 없이 크기 변화를 자동 처리할 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 콘텐츠에 따라 크기가 달라지는 텍스트 블록의 부드러운 expand/collapse 효과는 어떻게 구현하시겠습니까?">

가장 간단한 형태는 `Modifier.animateContentSize()` 한 줄을 텍스트 컨테이너에 추가하는 것입니다. expanded 플래그에 따라 표시할 텍스트(예: 한 줄짜리 요약 vs 여러 줄짜리 본문)를 바꾸면, animateContentSize 가 그 변화에 맞춰 컨테이너의 width/height 를 자동으로 보간해 줍니다. 별도의 애니메이션 코드 없이도 자연스러운 expand/collapse 가 만들어지고, 트윈(tween) 스펙도 파라미터로 직접 지정할 수 있어 디자인 시스템 톤에 맞춰 커스터마이즈가 쉽습니다.

조금 더 풍부한 표현이 필요하다면 `AnimatedVisibility` 와 결합하는 패턴이 자연스럽습니다. 한 줄 요약은 항상 보이도록 두고, 추가 본문 영역만 `AnimatedVisibility(visible = expanded, enter = expandVertically() + fadeIn(), exit = shrinkVertically() + fadeOut()) { ... }` 으로 감싸면, 펼침/접힘에 따라 본문이 들어오고 나가는 동안 페이드 효과까지 함께 적용됩니다. 이 두 기법을 합치면 "한 줄 요약 + 펼침 본문" 형태의 카드를 가장 적은 코드로 표현할 수 있습니다.

마지막으로 인터랙션 측면에서는 펼침 토글 버튼을 명확하게 노출하고, 접근성 관점에서 `Modifier.semantics { contentDescription = if (expanded) "본문 접기" else "본문 펼치기" }` 같은 시맨틱 속성을 함께 부여하는 것이 좋습니다. 또한 매우 긴 본문이라면 펼침 시점에 한꺼번에 측정 비용이 들어갈 수 있으므로, 본문 영역을 lazy 한 형태로 감싸 두거나 `animateContentSize` 의 `animationSpec` 을 짧게 잡아 시각적 부담을 줄이는 식의 마감을 권장합니다.

</def>
<def title="Q) 로딩 placeholder를 위한 시머(shimmer) 애니메이션 효과를 Canvas, Painter, 애니메이션 API로 어떻게 구현하시겠습니까?">

핵심 아이디어는 **그라디언트의 위치를 시간에 따라 이동시키는 것** 입니다. `rememberInfiniteTransition` 으로 0f→1f 사이를 무한 반복하는 progress 값을 만들고, `animateFloat` 으로 `RepeatMode.Restart` 와 적당한 duration(보통 1000~1500ms)을 설정합니다. 이 progress 값을 그라디언트의 시작/끝 좌표에 곱해 이동시키면, 빛이 표면을 가로지르는 듯한 시머 효과가 만들어집니다. 그라디언트는 보통 `Brush.linearGradient(colors = listOf(base, highlight, base), start = ..., end = ...)` 형태가 가장 자연스럽고, 양 끝의 base 색이 highlight 색을 감싸 자연스러운 페이드를 만들어 줍니다.

이 효과를 구현하는 자리는 두 가지 선택지가 있습니다. 가장 단순한 방법은 `Modifier.drawWithContent { ... }` 또는 `Modifier.drawBehind { ... }` 안에서 `drawRect(brush = shimmerBrush, blendMode = BlendMode.SrcOver)` 로 그라디언트 사각형을 그려 주는 것입니다. 이 경우 시머는 그 컴포저블의 영역을 덮는 표면처럼 동작하고, placeholder 도형은 별도의 컴포저블로 그려 두면 됩니다. 더 재사용성을 높이고 싶다면 `Painter` 를 직접 만들어 `onDraw` 안에 같은 그라디언트 로직을 두고, 어디서든 `Image(painter = shimmerPainter)` 형태로 호출 가능한 컴포넌트로 발전시킬 수 있습니다. 이 방식은 디자인 시스템의 placeholder 컴포넌트로 묶어 두기 좋습니다.

마무리는 **활성/비활성 토글** 입니다. 데이터 로딩이 끝났을 때 시머가 더 이상 동작하지 않아야 하므로, isLoading 상태에 따라 `Modifier.then(if (isLoading) Modifier.shimmer() else Modifier)` 처럼 modifier 자체를 분기하거나, 그리기 람다 안에서 progress 값을 토글에 맞춰 0 으로 고정하는 식으로 처리합니다. 또한 `graphicsLayer { compositingStrategy = CompositingStrategy.Offscreen }` 을 함께 적용하면 여러 placeholder 가 동시에 시머 효과를 가질 때 합성 비용을 안정적으로 유지할 수 있습니다.

</def>
</deflist>
