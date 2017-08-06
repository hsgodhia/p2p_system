class PeerInterface:
    #when called on a peer X, X updates the score of peerIdY passed as a param
    def was_hit(self, peerIdY, hitstatus):
        pass
    
    #when called on a peer X, X communicates by flooding to the network an approaching bird at pointY subject to hopcount
    def bird_approaching(self, pointY, hopcount):
        pass

    #when called on a peer X, X requests peerIdY to reply with its hit status (via its network topology neighbors)
    def status(self, peerIdY):
        pass

    #when called on peer X, X requests all peers in the p2p network to respond with was_hit messages regarding their hitstatus
    #hitstatus = True if pig is hit/die False otherwise/alive
    def status_all(self):
        pass

    #when called on peer X, X informs peerIdY (a param) that it was hit
    def take_shelter(self, peerIdY):
        pass
