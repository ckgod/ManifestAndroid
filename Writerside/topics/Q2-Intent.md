# Q2) Intent

## Intent란? {#what-is-intent}
Intent는 수행할 작업에 대한 추상적인 설명이다. 이는 Activity, Service, BroadCast Receiver가 통신할 수 있도록 하는 **메시징 객체** 역할을 한다.
일반적으로 Activity를 시작하거나, BroadCast를 보내거나, Service를 시작하는데 사용된다.
또한 컴포넌트 간 데이터를 전달할 수 있으므로 안드로이드 컴포넌트 기반 아키텍처의 기본 요소이다.

Android에는 **명시적 Intent**와 **암시적 Intent** 두 가지 주요 유형이 있다.


### 명시적 Intent {#explicit-intent}
- **정의**: 명시적 인텐트는 직접 이름을 지정하여 호출할 정확한 Component(Activity, Service..)를 지정한다.
- **사용 사례**: 명시적 인텐트는 대상 Component를 알고 있을 때 사용된다.
- **시나리오**: 동일한 앱 내에서 Activity간 전환하는 경우 명시적 인텐트가 사용된다.


```Kotlin
// Explicit Intent.kt
val intent = Intent(this, TargetActivity::class.java)
startActivity(intent)
```

### 암시적 Intent {#inplicit-intent}
- **정의**: 암시적 인텐트는 특정 컴포넌트를 지정하지 않고 수행해야 할 일반적인 작업을 선언한다. 시스템은 `action`, `category` 및 `data`에 따라 해당 인텐트를 처리할 수 있는 컴포넌트를 결정한다.
- **사용 사례**: 암시적 인텐트는 다른 앱이나 시스템 구성 요소가 처리할 수 있는 작업(예: URL 열기 또는 콘텐츠 공유)을 수행하려는 경우에 유용하다.
- **시나리오**: 브라우저에서 웹 페이지를 열거나 다른 앱과 콘텐츠를 공유하는 경우 암시적 인텐트를 사용한다. 시스템이 해당 Intent를 처리할 앱을 결정한다.

```Kotlin
// Inplicit Intent.kt
val intent = Intent(Intent.ACTION_VIEW)
intent.data = Uri.parse("https://www.example.com")
startActivity(intent)
```
{title="Inplicit Intent.kt"}

### 요약 {#intent-summary}
명시적 인텐트는 대상 컴포넌트가 알려진 **내부 앱 탐색**에 사용된다. 반면 암시적 인텐트는 대상을 직접 지정하지 않고 **외부 앱이나 다른 컴포넌트에서 처리할 수 있는 작업**에 사용된다.
이를 통해 안드로이드 생태계가 더욱 유연해지고 앱이 원활하게 상호 작용할 수 있다.

### Intent Filter란?
인텐트 필터는 앱 컴포넌트가 링크 열기 또는 BroadCast 처리와 같은 특정 인텐트에 응답하는 방법을 정의한다.
인텐트 필터는 인텐트 유형을 선언하는 필터 역할을 한다.

가장 대표적인 예시는 다른 앱의 `공유하기` 메뉴에 자신의 앱을 노출시키는 것.

> 암시적 Intent가 전송되면, Android 시스템은 설치된 앱의 manifest 파일에 정의된 intent filter와 Intent의 속성을 일치시켜 실행할 적절한 구성 요소를 결정합니다. 일치하는 항목이 발견되면 시스템은 해당 구성 요소를 시작하고 Intent 객체를 전달합니다. 여러 구성 요소가 Intent와 일치하는 경우, 시스템은 사용자에게 선택 대화 상자(chooser dialog)를 제공하여 해당 작업을 처리하는 데 선호하는 앱을 선택할 수 있도록 합니다.

![intent-filter.png](intent-filter.png)

#### 1. AndroidManifest.xml 설정
처리하고자 하는 액티비티의 `<activity>` 태그 내부에 `<intent-filter>`를 선언.

```xml
<activity android:name=".ShareActivity">
    <intent-filter>
        <action android:name="android.intent.action.SEND" />
        
        <category android:name="android.intent.category.DEFAULT" />
        
        <data android:mimeType="text/plain" />
    </intent-filter>
</activity>
```
위 설정은 "우리 앱의 `ShareActivity`는 `text/plain` 타입의 데이터를 `SEND`하는 액션을 처리할 수 있다"고 안드로이드 시스템에 등록하는 역할을 한다.

#### 2. Activity에서 데이터 받기
이제 `ShareActivity`의 `onCreate`메서드에서 인텐트로 전달된 텍스트를 받아서 처리한다.

```Kotlin
class ShareActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_share)

        // 인텐트의 액션과 타입이 일치하는지 확인
        if (intent?.action == Intent.ACTION_SEND && "text/plain" == intent.type) {
            
            // Intent.EXTRA_TEXT 키로 공유된 텍스트를 꺼냅니다.
            val sharedText = intent.getStringExtra(Intent.EXTRA_TEXT)

            // 받아온 텍스트를 토스트 메시지 등으로 활용
            Toast.makeText(this, sharedText, Toast.LENGTH_SHORT).show()
        }
    }
}
```
이제 다른 앱(브라우저, 메모장 등)에서 텍스트를 선택하고 공유 버튼을 누르면, 공유 대상 목록에 우리 앱이 나타나게 된다.


#### 사용 예시
다른 앱에서 텍스트를 공유할 때, 내 앱의 ShareActivity가 선택지에 나타나도록 만드는 간단한 예제이다.


> Q) 명시적 인텐트와 암시적 인텐트의 주요 차이점은 무엇이고 어떤 시나리오에서 사용되나요?
>
> Q) 안드로이드 시스템은 암시적 인텐트를 처리할 앱을 어떻게 결정하고, 적합한 앱이 없을 경우 어떻게 되나요?