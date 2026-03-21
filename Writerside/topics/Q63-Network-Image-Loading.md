# Q63) 네트워크 이미지 로딩

## 네트워크에서 이미지를 어떻게 가져와 화면에 표시하나요? {#how-to-fetch-and-render-images}

이미지 로딩은 사용자 프로필이나 네트워크에서 받아 온 콘텐츠를 보여 주는 등, 현대 애플리케이션 개발에서 핵심적인 요소입니다. 직접 이미지 로딩 시스템을 만들어 보는 것도 가능하지만, 네트워크 요청, 이미지 리사이징, 캐싱, 렌더링, 효율적인 메모리 관리 같은 기능을 모두 직접 구현해야 한다는 부담이 있습니다. 그래서 일반적으로는 **Glide**, **Coil**, **Fresco** 같은 검증된 라이브러리를 사용해 이런 작업을 위임합니다. 이들 라이브러리는 다운로드, 캐싱, 렌더링을 자연스럽게 처리해 주므로 개발자는 비즈니스 로직과 UX에 집중할 수 있습니다.

### Glide {#glide}

[Glide](https://github.com/bumptech/glide)는 빠르고 효율적인 이미지 로딩 라이브러리로, Android 커뮤니티에서 오랜 시간 자리를 지켜 온 선택지입니다. 캐싱, 플레이스홀더, 이미지 변환 같은 복잡한 시나리오를 다루기에 적합합니다. Google의 공식 오픈 소스 프로젝트를 비롯해 수많은 글로벌 제품과 오픈 소스 프로젝트에서 사용되고 있습니다.

```kotlin
Glide.with(context)
    .load("https://example.com/image.jpg")
    .placeholder(R.drawable.placeholder)
    .error(R.drawable.error_image)
    .into(imageView)
```
{title="GlideExample.kt"}

Glide는 자동으로 이미지를 캐싱해 네트워크 호출을 최적화하고 성능을 향상시킵니다. 애니메이션 GIF 지원, [플레이스홀더](https://bumptech.github.io/glide/doc/placeholders.html), [이미지 변환(transformations)](https://bumptech.github.io/glide/doc/transformations.html), [캐싱](https://bumptech.github.io/glide/doc/caching.html), [리소스 재사용](https://bumptech.github.io/glide/doc/resourcereuse.html) 등 다양한 기능을 제공합니다.

### Coil {#coil}

[Coil](https://github.com/coil-kt/coil)은 Android를 위해 설계된 Kotlin 우선 이미지 로딩 라이브러리입니다. **Coroutines** 위에서 동작하며 Jetpack Compose 같은 최신 기능을 자연스럽게 지원합니다. 특히 Coil은 Android 프로젝트에서 이미 널리 쓰이는 [OkHttp](https://square.github.io/okhttp/)와 [Coroutines](https://kotlinlang.org/docs/coroutines-overview.html)를 활용하기 때문에, 다른 대안에 비해 더 가볍다는 장점이 있습니다.

```kotlin
imageView.load("https://example.com/image.jpg") {
    placeholder(R.drawable.placeholder)
    error(R.drawable.error_image)
    transformations(CircleCropTransformation())
}
```
{title="CoilExample.kt"}

Coil은 Kotlin과 Jetpack Compose에 매끄럽게 통합되며 [이미지 변환](https://coil-kt.github.io/coil/transformations/), [애니메이션 GIF 지원](https://coil-kt.github.io/coil/gifs/), [SVG 렌더링](https://coil-kt.github.io/coil/svgs/), [비디오 프레임 추출](https://coil-kt.github.io/coil/videos/) 같은 유용한 기능을 함께 제공합니다. 가벼운 무게 덕분에 최신 Android 프로젝트에 잘 어울립니다.

이미지 로딩 라이브러리 중에서도 Coil은 현재 가장 활발하게 유지보수되고 있으며, Jetpack Compose, Kotlin Multiplatform 등 최근 Android 솔루션에 대한 지원이 강력합니다. Kotlin 우선 접근과 꾸준한 업데이트 덕분에 오늘날 개발자 커뮤니티에서 가장 선호되는 옵션 중 하나가 되었습니다.

### Fresco {#fresco}

[Fresco](https://github.com/facebook/fresco)는 [Meta](https://github.com/facebook)에서 만든 이미지 로딩 라이브러리로, 고급 사용 사례를 염두에 두고 설계되었습니다. 자체적인 이미지 디코딩·표시 파이프라인을 통해 다른 라이브러리들과는 다른 접근을 취합니다.

```kotlin
val draweeView: SimpleDraweeView = findViewById(R.id.drawee_view)
draweeView.setImageURI("https://example.com/image.jpg")
```
{title="FrescoExample.kt"}

Fresco를 쓰려면 XML에 Fresco 위젯을 사용해야 합니다.

```xml
<com.facebook.drawee.view.SimpleDraweeView
    android:id="@+id/drawee_view"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content" />
```
{title="fresco_layout.xml"}

Fresco는 큰 이미지 처리, 점진적 렌더링, 고급 캐싱 전략에 강해 메모리 제약이 큰 애플리케이션에서 효율적으로 동작합니다. Android 4.x 이하에서는 이미지를 별도의 메모리 영역에 할당해 성능을 끌어올렸지만, 해당 디바이스의 사용이 점점 줄면서 그 이점은 옅어지는 추세입니다. 그럼에도 불구하고 이미지 파이프라인, drawee, 최적화된 메모리 관리, 고급 로딩 메커니즘, 스트리밍, 애니메이션 같은 견고한 기능을 여전히 제공하므로, 복잡한 이미지 처리가 필요한 프로젝트에는 충분히 검토할 가치가 있습니다.

### 요약 {#summary}

<tldr>
각 라이브러리는 고유의 강점을 가지고 있습니다. **Glide** 는 다양한 시나리오에 두루 쓰이는 검증된 라이브러리로, Compose 지원이 오랜 시간 베타 단계에 머물고 있다는 점은 약점입니다. **Coil** 은 Kotlin 중심·경량·Compose/KMP 지원이라는 강점으로 최신 Android 개발에 가장 자연스럽게 어울립니다. **Fresco** 는 점진적 렌더링과 고급 이미지 파이프라인이 필요한 메모리 집약적 시나리오에서 좋은 선택입니다. 어떤 라이브러리를 고르더라도 적절한 캐싱, 에러 처리, 자원 관리는 부드러운 사용자 경험을 위해 반드시 챙겨야 합니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 원격 서버에서 고해상도 이미지를 불러와 RecyclerView에서 부드러운 스크롤을 유지하면서 표시하려면 어떤 이미지 로딩 라이브러리를 선택하고, UI 지연을 막기 위해 어떤 최적화를 적용하시겠습니까?">

가장 합리적인 1순위 선택은 **Coil** 입니다. Kotlin 우선이라 코루틴 기반 코드와 자연스럽게 결합되고, Jetpack Compose나 RecyclerView 어느 쪽이든 동일한 호출 패턴으로 다룰 수 있어 코드가 깔끔하게 유지됩니다. 만약 프로젝트가 이미 Glide 생태계 위에 있다면 Glide 역시 좋은 선택이며, 메모리 제약이 매우 큰 애플리케이션에서는 Fresco의 파이프라인이 추가적인 이점을 줄 수 있습니다.

스크롤 성능을 위해서는 라이브러리 사용법을 넘어 몇 가지 최적화를 함께 챙겨야 합니다. 먼저 ImageView의 실제 표시 크기에 맞춰 다운샘플링된 이미지를 받아 오도록 만들어야 합니다. Coil은 ImageView 사이즈를 자동으로 추정해 디코딩하지만, 명시적으로 `size(...)` 또는 `Size`를 설정하면 더 안정적입니다. 또한 RecyclerView가 뷰를 재활용할 때 이전 요청을 취소해야 합니다. Coil은 ImageView에 새 요청을 시작하면 이전 요청을 자동으로 취소하지만, 직접 `dispose()`나 라이브러리별 취소 API를 호출해야 하는 경우도 있습니다.

캐싱과 디코딩 전략도 핵심입니다. 메모리 캐시와 디스크 캐시를 모두 활성화하고, 큰 이미지를 디코딩하는 경우 `RGB_565` 같은 더 저렴한 비트맵 설정을 고려할 수 있습니다. 마지막으로 placeholder/에러 이미지 같은 즉시 표시 가능한 자원을 사용해 첫 프레임이 비어 보이지 않도록 만들면, 체감 스크롤 성능이 크게 향상됩니다.

</def>
</deflist>
