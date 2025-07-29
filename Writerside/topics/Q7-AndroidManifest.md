# Q7) AndroidManifest

## `AndroidManifest.xml` 파일의 용도는 무엇인가요?
`AndroidManifest.xml`파일은 안드로이드 프로젝트에서 애플리케이션에 대한 필수 정보를 안드로이드 OS에 정의하는 중요한 구성 파일이다.
이 파일은 앱의 컴포넌트, 권한, 하드웨어 및 소프트웨어 기능 등을 알려주며 애플리케이션과 OS간 다리 역할을 한다.

### `AndroidManifest.xml`의 주요 기능 {#feature-manifest}
1. **애플리케이션 구성요소 선언**: 안드로이드 시스템이 앱의 구성요소를 어떻게 시작하고 상호작용할지 알 수 있도록 Activity, Service, Broadcast Receiver, Content Provider와 같은 필수 구성요소를 등혹한다.
2. **권한 선언**: 앱이 필요로 하는 권한(예: `INTERNET`, `ACCESS_FINE_LOCATION`, `READ_CONTACTS`)을 선언한다. 이를 통해 사용자는 앱이 어떤 리소스에 접근할 것인지 알 수 있으며, 이 권한들을 허용하거나 거부할 수 있다.
3. **하드웨어 및 소프트웨어 요구사항**: 앱이 의존하는 기능(예: 카메라, GPS, 특정 화면 크기)을 명시한다. 이는 Play 스토어가 이러한 요구사항을 충족하지 못하는 기기를 필터링하는 데 도움을 준다.
4. **앱 메타데이터**: 앱의 패키지 이름, 버전, 최소 및 대상 API 레벨, 테마, 스타일과 같은 필수 정보를 제공한다. 이 정보는 시스템이 앱을 설치하고 실행하는 데 사용된다.
5. **인텐트 필터**: `Activity`와 같은 구성요소가 어떤 종류의 인텐트(Intent)에 응답할 수 있는지를 지정한다. 예를 들어, 링크를 열거나 콘텐츠를 공유하는 등의 작업을 명시하여 다른 앱이 내 앱과 상호작용할 수 있게 한다.
6. **앱 환경설정 및 세팅**: 메인 런처 액티비티 설정, 백업 동작 구성, 테마 지정과 같이 앱이 어떻게 동작하고 표시될지를 제어하는 환경설정을 포함한다.

### `AndroidManifiest.xml`예시

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />

    <application
            android:allowBackup="true"
            android:icon="@mipmap/ic_launcher"
            android:label="@string/app_name"
            android:theme="@style/AppTheme">

        <activity android:name=".MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <service android:name=".MyService" />
        <receiver android:name=".MyBroadcastReceiver" />

    </application>
</manifest>
```

### 요약
`AndroidManifest.xml` 파일은 모든 안드로이드 앱의 기초이며, 안드로이드 OS가 앱의 생명주기, 권한, 그리고 상호작용을 관리하는 데 필요한 상세 정보를 제공한다.
이 파일은 본질적으로 앱의 구조와 요구사항을 정의하는 **청사진(bluepring)** 역할을 한다.

> Q) `AndroidManifest`의 인텐트 필터는 어떻게 앱 간의 상호작용을 가능하게 하며, 만약 Activity 클래스가 `AndroidManifest`에 등록되지 않으면 어떤 일이 발생하나요?
