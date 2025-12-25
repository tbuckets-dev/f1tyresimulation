token_secret = "3096facb-4a43-4ea9-bf6e-6df50bd8121f"
token_id = "terraform@pve!terraform-token"
ciuser = "taylor"
cipassword = "Slr1v2i2!"

ssh_private_key = <<EOF
    -----BEGIN RSA PRIVATE KEY-----
    b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAArAAAABNlY2RzYS
    1zaGEyLW5pc3RwNTIxAAAACG5pc3RwNTIxAAAAhQQBhqxSI1y44a8n7cdOldnabvpVEUj6
    0sdLpSgpl+NEx/5A2kEwHo++Pnz2BimSnBX0BfNyTiqr9BXDkvo0FWgi4AsBLJSR3YmPUX
    xOs5bIXQGSNzS1ac4Xg0eAKEXi4oEq2XtcFmB4F+N/YdHHXCOG+yqEF+2bsYuIJs5zcUsR
    XPX69EAAAAEI2xuJcdsbiXEAAAATZWNkc2Etc2hhMi1uaXN0cDUyMQAAAAhuaXN0cDUyMQ
    AAAIUEAYasUiNcuOGvJ+3HTpXZ2m76VRFI+tLHS6UoKZfjRMf+QNpBMB6Pvj589gYpkpwV
    9AXzck4qq/QVw5L6NBVoIuALASyUkd2Jj1F8TrOWyF0Bkjc0tWnOF4NHgChF4uKBKtl7XB
    ZgeBfjf2HRx1wjhvsqhBftm7GLiCbOc3FLEVz1+vRAAAAAQgDdF6oc6TllG2tNhJMhyh6i
    +EZkF8YkXuOqJQ4hg1a1EuQ+BXAXpDuBCG/bgyhcyV8tKhEHwyW8vt75oTITZWwcwgAAAA
    p0YXlsb3JAc3J2
    -----END RSA PRIVATE KEY-----
    EOF

ssh_key = <<EOF
    ecdsa-sha2-nistp521 AAAAE2VjZHNhLXNoYTItbmlzdHA1MjEAAAAIbmlzdHA1MjEAAACFBAGGrFIjXLjhryftx06V2dpu+lURSPrSx0ulKCmX40TH/kDaQTAej74+fPYGKZKcFfQF83JOKqv0FcOS+jQVaCLgCwEslJHdiY9RfE6zlshdAZI3NLVpzheDR4AoReLigSrZe1wWYHgX439h0cdcI4b7KoQX7Zuxi4gmznNxSxFc9fr0QA== taylor@srv
    EOF

