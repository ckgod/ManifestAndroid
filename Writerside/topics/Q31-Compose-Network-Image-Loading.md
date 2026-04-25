# Q31) Compose에서 네트워크 이미지 로딩

## Compose에서 네트워크 이미지를 어떻게 불러오나요? {#how-to-load-network-images}

Jetpack Compose 자체는 네트워크 이미지 로딩을 위한 기본 지원을 포함하지 않습니다. 대신 **Coil**, **Glide**, **Landscapist** 같은 서드파티 라이브러리를 사용해 URL로부터 이미지를 효율적으로 불러와 표시할 수 있습니다. 이 라이브러리들은 Jetpack Compose나 Kotlin Multiplatform 환경과 자연스럽게 통합되며, 캐싱이나 placeholder 처리 같은 최적화도 함께 제공합니다.

직접 이미지 로딩 시스템을 만들어 보는 일도 가능하지만, 네트워크 다운로드, 리사이징, 캐싱, 렌더링, 효율적인 메모리 관리 같은 부분들을 모두 직접 다뤄야 합니다. 이 영역은 매끄러운 성능과 자원 사용을 보장하기 위해 세심한 최적화가 필요한 만큼, 일반적으로는 이미 검증된 이미지 로딩 라이브러리를 사용하는 것이 권장됩니다. 캐싱, 변환(transformations), 비동기 로딩까지 잘 다듬어진 형태로 제공되어 직접 만드는 일에 비해 비용이 훨씬 작습니다.

### Coil {#coil}

[Coil](https://github.com/coil-kt/coil)은 Jetpack Compose와 Kotlin Multiplatform에 최적화된 이미지 로딩 라이브러리입니다. 전체가 Kotlin 으로 작성되어 있고, 노출되는 API도 Kotlin 친화적입니다. 또한 OkHttp와 Coroutines처럼 Android 프로젝트에서 이미 폭넓게 사용되는 라이브러리들을 활용해 구현되어 있어 다른 대안에 비해 더 가볍습니다. Compose 지원과 함께 변환, 애니메이션 GIF, SVG, 비디오 프레임 같은 유용한 기능들을 제공합니다.

```kotlin
AsyncImage(
    model = "https://example.com/image.jpg",
    contentDescription = null,
)
```
{title="CoilExample.kt"}

### Glide {#glide}

[Glide](https://github.com/bumptech/glide)는 Android에서 가장 널리 쓰여 온 이미지 로딩 라이브러리 중 하나입니다. Compose 지원도 제공하지만, 2023년 9월 시점 기준으로 Compose 통합이 베타 단계에 머물러 있고 이후 큰 업데이트가 없는 상태입니다. 그럼에도 애니메이션 GIF, placeholder, 변환, 캐싱, 자원 재사용 같은 견고한 기능을 제공해 Android 앱에서 이미지를 다루는 데 충분히 신뢰할 수 있는 선택지입니다.

```kotlin
GlideImage(
    model = myUrl,
    contentDescription = stringResource(R.string.picture_of_cat),
    modifier = Modifier
        .padding(padding)
        .clickable(onClick = onClick)
        .fillParentMaxSize(),
)
```
{title="GlideExample.kt"}

> Glide는 한때 Google의 한 엔지니어가 단독으로 유지보수해 왔지만, 그 메인테이너가 다른 회사로 옮긴 이후 활발한 유지보수가 줄었고 2023년 9월 이후 새 릴리스가 거의 없는 상태로 알려져 있습니다.

### Landscapist {#landscapist}

[Landscapist](https://github.com/skydoves/landscapist)는 Glide, Coil, Fresco의 코어를 활용해 네트워크나 로컬 자원에서 이미지를 효율적으로 가져와 표시하기 위해 설계된 Jetpack Compose · Kotlin Multiplatform 이미지 로딩 라이브러리입니다. Jetpack Compose의 성능에 초점을 맞춰 설계되어 있으며, 리컴포지션 오버헤드를 줄이는 부분에 신경을 많이 썼습니다. 대부분의 컴포저블 함수가 **Restartable** 이고 **Skippable** 이라, Compose Compiler 메트릭에서 보더라도 리컴포지션 효율이 좋습니다.

또한 **Baseline Profile** 을 활용해 시작 시간과 런타임 실행을 최적화하며, ImageOptions, 상태 리스너, 커스텀 컴포저블 지원, Android Studio 프리뷰 호환, ImageComponent · ImagePlugin 같은 모듈형 컴포넌트 등 광범위한 커스터마이즈 옵션을 제공합니다. placeholder, 애니메이션(circular reveal, crossfade), 변환(blur), 컬러 팔레트 추출 같은 고급 기능도 함께 갖추고 있어 Compose 환경의 이미지 로딩에 유연한 도구가 됩니다.

```kotlin
GlideImage( // CoilImage, FrescoImage 도 동일한 패턴으로 사용 가능
    imageModel = { imageUrl },
    modifier = modifier,
    component = rememberImageComponent {
        // 로딩 중에 시머 효과를 보여 줍니다.
        +ShimmerPlugin(
            Shimmer.Flash(
                baseColor = Color.White,
                highlightColor = Color.LightGray,
            ),
        )
    },
    // 요청이 실패하면 에러 텍스트를 보여 줍니다.
    failure = {
        Text(text = "image request failed.")
    }
)
```
{title="LandscapistGlideExample.kt"}

### 요약 {#summary}

<tldr>

이미지 로딩은 사용자 프로필이나 네트워크 콘텐츠를 보여 주는 작업에서 빠지지 않는 요소입니다. **Coil**, **Glide**, **Landscapist** 같은 라이브러리를 사용하면 네트워크 이미지를 효율적으로 불러올 뿐 아니라 변환, 애니메이션 GIF, SVG, 비디오 프레임 같은 다양한 플러그인 지원까지 함께 누릴 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Jetpack Compose에서 사용해 본 서드파티 이미지 로딩 라이브러리는 어떤 것이 있고, 각각의 트레이드오프는 무엇인가요?">

가장 무난한 1순위는 **Coil** 입니다. Kotlin 우선 설계 + Compose 친화적인 API + OkHttp/Coroutines 기반의 가벼운 의존성이라는 조합 덕분에, 새 Compose 프로젝트에 큰 고민 없이 도입할 수 있습니다. `AsyncImage` 한 줄로 기본 동작을 만들 수 있고, `placeholder`, `error`, `transformations` 같은 옵션도 람다 형태로 자연스럽게 확장됩니다. 단점이라면 매우 깊은 커스터마이즈가 필요한 경우(특히 placeholder/transition을 디자인 시스템 단위로 다듬어야 할 때) 직접 wrapper 컴포저블을 한 겹 만들어야 한다는 정도입니다.

**Glide** 는 오랜 트랙 레코드와 풍부한 기능 덕분에 여전히 유효한 선택입니다. 비트맵 풀, 트랜지션, 메모리/디스크 캐시 정책 등 세밀한 제어 옵션을 제공해, 이미지가 화면의 핵심 자원인 앱(예: 갤러리, 미디어 큐레이션)에서 잘 어울립니다. 다만 Compose 통합이 베타에 오래 머물러 있고 최근 업데이트 빈도가 낮다는 점은 의사결정 시 고려해야 합니다. 새 Compose 프로젝트라면 굳이 Glide를 들여올 이유는 적고, 이미 Glide 기반으로 짜인 레거시 화면을 점진적으로 Compose로 옮길 때 자연스러운 가교 역할을 하는 정도가 가장 자연스러운 자리입니다.

**Landscapist** 는 Compose 생태계에 정확히 맞춰 설계된 라이브러리라는 점이 가장 큰 차별점입니다. 컴포저블의 stability, Baseline Profile, ImageComponent/ImagePlugin 같은 Compose 친화적 추상화를 제공해, 시머·crossfade·블러·팔레트 추출 같은 효과를 호출 측 코드로 깔끔하게 표현할 수 있습니다. 또한 Glide/Coil/Fresco 어느 코어든 같은 API 위에서 골라 쓸 수 있어, 이미지 로딩 전략을 바꾸더라도 화면 코드를 거의 손대지 않아도 된다는 이점이 있습니다. 트레이드오프는 추가 의존성이 한 겹 늘어난다는 점이며, 이 비용을 디자인 시스템 일관성과 Compose 친화성으로 갚을 수 있는지가 도입 판단 기준이 됩니다.

</def>
</deflist>
