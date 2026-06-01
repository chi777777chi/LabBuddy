import reflex as rx


class WebViewGuard(rx.Component):
    """在 React render 時同步偵測 WebView UA，不依賴 WebSocket 或 DOM 操作。"""

    tag = "WebViewGuard"
    backend_url: rx.Var[str] = ""

    def _get_custom_code(self) -> str:
        return r"""
        function WebViewGuard({ backendUrl }) {
            const ua = navigator.userAgent || '';
            const isWV =
                /FBAN|FBAV|Instagram|Line\/|MicroMessenger|WeChat|GSA/.test(ua) ||
                (/iPhone|iPad|iPod/.test(ua) && !ua.includes('Version/')) ||
                (/Android/.test(ua) && /wv/.test(ua));

            if (isWV) {
                return (
                    <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:'12px',width:'100%'}}>
                        <div style={{background:'var(--orange-3)',border:'1px solid var(--orange-6)',padding:'12px 16px',borderRadius:'8px',width:'100%',boxSizing:'border-box'}}>
                            <strong>⚠️ 請用 Safari 或 Chrome 開啟此頁面</strong>
                        </div>
                        <p style={{color:'var(--gray-11)',fontSize:'14px',textAlign:'center',margin:0}}>
                            在 LINE、Instagram 等 App 內開啟連結時，Google 會拒絕登入。請複製網址後用 Safari 或 Chrome 開啟。
                        </p>
                        <button
                            onClick={() => navigator.clipboard.writeText(window.location.href)}
                            style={{width:'100%',padding:'10px',background:'var(--orange-9)',color:'white',border:'none',borderRadius:'8px',fontSize:'16px',cursor:'pointer'}}>
                            📋 複製網址
                        </button>
                    </div>
                );
            }

            return (
                <button
                    onClick={() => { window.location.href = backendUrl + '/auth/google'; }}
                    style={{width:'100%',padding:'10px 16px',background:'var(--accent-9)',color:'white',border:'none',borderRadius:'8px',fontSize:'16px',cursor:'pointer',display:'flex',alignItems:'center',justifyContent:'center',gap:'8px'}}>
                    <span>&#x2192;</span>
                    <span>使用 Google 帳號登入</span>
                </button>
            );
        }
        """
